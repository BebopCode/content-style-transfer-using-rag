from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from fastapi.middleware.cors import CORSMiddleware
from .database import get_db, Base, engine
from . import models # schemas are Pydantic models for request/response
from .schemas import EmailCreate, Generate
from .pos_tagging import extract_top_words
from typing import Tuple,List
from .models import EmailDB
import os
from google import genai
from email.parser import BytesParser
from email import policy
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime
from fastapi import Form
from .chroma import EmailEmbeddingStore
from .extract_from_eml import parse_eml_bytes

Base.metadata.create_all(bind=engine)
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # <- allows all domains
    allow_credentials=True,
    allow_methods=["*"],             # <- allows all HTTP methods
    allow_headers=["*"],             # <- allows all headers
)

# Example Pydantic Schema for input validation
@app.get("/recipients/{sender_email}")
async def get_recipients(
    sender_email: str,
    db: Session = Depends(get_db)
):
    """
    Get all unique recipients that a sender has sent emails to.
    """
    recipients = db.query(
        EmailDB.receiver,
        func.count(EmailDB.receiver).label('count')
    ).filter(
        EmailDB.sender == sender_email
    ).group_by(
        EmailDB.receiver
    ).order_by(
        func.count(EmailDB.receiver).desc()
    ).all()
    
    return [
        {"email": recipient[0], "count": recipient[1]} 
        for recipient in recipients if recipient[0]
    ]

    

@app.post("/upload-emails/")
async def upload_emails(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload multiple .eml files and store them in the database.
    """
    results = {
        "success": [],
        "failed": [],
        "skipped": []
    }
    email_embedding_store = EmailEmbeddingStore()
    for file in files:
        # Check if file is .eml
        if not file.filename.endswith('.eml'):
            results["failed"].append({
                "filename": file.filename,
                "error": "Not an .eml file"
            })
            continue
        
        try:
            # Read file content
            content = await file.read()
            
            # Parse the .eml file
            email_data = parse_eml_bytes(content)
            
            # Check if message_id exists
            if not email_data["message_id"]:
                results["failed"].append({
                    "filename": file.filename,
                    "error": "No message ID found"
                })
                continue
            
            # Check if email already exists in database
            existing_email = db.query(EmailDB).filter(
                EmailDB.message_id == email_data["message_id"]
            ).first()
            
            if existing_email:
                results["skipped"].append({
                    "filename": file.filename,
                    "message_id": email_data["message_id"],
                    "reason": "Already exists in database"
                })
                continue
            
            # Create new email record
            new_email = EmailDB(**email_data)
            try:
                email_embedding_store.add_email(new_email)
                
            except Exception as e:
                    # Note: ChromaDB errors are separate from DB errors.
                    # You might choose to log this error and skip the DB add, 
                    # or continue with the DB add and handle the missing embedding later.
                print(f"ChromaDB Error for message_id {new_email['message_id']}: {e}")
                    # We'll continue to add to the relational DB for robustness,
                    # assuming the primary data is more critical than the embedding.
                    
                # 3. Add the email object to the SQLAlchemy session

            db.add(new_email)
            db.commit()
            
            results["success"].append({
                "filename": file.filename,
                "message_id": email_data["message_id"],
                "subject": email_data["subject"]
            })
            
        except Exception as e:
            db.rollback()
            results["failed"].append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "total_files": len(files),
        "successful": len(results["success"]),
        "failed": len(results["failed"]),
        "skipped": len(results["skipped"]),
        "details": results
    }

@app.get("/emails/conversation/{sender}/{receiver}")
async def get_conversation(
    sender: str,
    receiver: str,
    db: Session = Depends(get_db)
):
    """
    Get all emails between two people (bidirectional).
    """
    emails = db.query(EmailDB).filter(
        or_(
            and_(EmailDB.sender == sender, EmailDB.receiver == receiver),
        )
    ).order_by(EmailDB.sent_at.desc()).all()
    
    # Convert to dict for JSON serialization
    result = []
    for email in emails:
        result.append({
            "message_id": email.message_id,
            "parent_message_id": email.parent_message_id,
            "references": email.references,
            "sender": email.sender,
            "receiver": email.receiver,
            "subject": email.subject,
            "content": email.content,
            "sent_at": email.sent_at.isoformat() if email.sent_at else None
        })
    
    return result

def get_historical_content(db: Session, sender: str, receiver: str) -> Tuple[str, List[str]]:
    """
    Retrieves and concatenates all 'content' from emails where the 
    original 'receiver' sent the email to the original 'sender'.
    Also fetches the content of the 3 most recent emails in that conversation.
    
    Condition: EmailDB.sender == receiver AND EmailDB.receiver == sender (for all emails)
    
    Returns: A tuple (concatenated_content, recent_emails_content_list)
    """
    
    # 1. Define the specific filter condition for the Receiver -> Sender direction
    filter_condition = (EmailDB.sender == receiver) & (EmailDB.receiver == sender)
    
    # --- Fetch ALL matching content for concatenation ---
    historical_emails_all = db.query(EmailDB.content).filter(
        filter_condition
    ).limit(100).all()
    
    # Extract and concatenate content
    content_list_all = [c[0] for c in historical_emails_all]
    concatenated_content = "\n\n---\n\n".join(content_list_all)

    # --- Fetch the 3 MOST RECENT email contents ---
    # We apply the same filter, but order by timestamp descending and limit to 3.
    historical_emails_recent = db.query(EmailDB.content).filter(
        filter_condition
    ).order_by(
        EmailDB.sent_at.desc() # Assumes a 'timestamp' column exists
    ).limit(3).all()

    # Extract the content for the recent emails
    recent_emails_content_list = [c[0] for c in historical_emails_recent]

    # Return both the concatenated string and the list of recent email content
    return concatenated_content, recent_emails_content_list



### 2. ⚡ The FastAPI Endpoint
@app.post("/api/generate")
async def generate_email(
    data: Generate, 
    db: Session = Depends(get_db)
):
    """
    Endpoint to retrieve historical email content between a sender and receiver,
    and concatenate it for use (e.g., in a RAG or prompt context).
    """
    
    # 1. Extract clean, stripped values from the input model
    clean_sender = data.sender.strip()
    clean_receiver = data.receiver.strip()
    custom_prompt = data.custom_prompt
    
    # 2. Use the database function to retrieve concatenated historical content
    historical_context, recent_emails = get_historical_content(
        db, 
        sender=clean_sender, 
        receiver=clean_receiver
    )
    features = extract_top_words(historical_context)
    
    # 3. Compile all information into a final context object for the next step passing to the  
    additional_context = custom_prompt
    
    final_context_object = {
        "person_I_want_to_reply_to": clean_sender,
        "my_email": clean_receiver,
        "my_stylometric_features": features,
        "mail_I_want_to_reply_to": data.content,
    }
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing client. Check your API key. Error: {e}")
        return
    
    prompt = f"""
    You are an email-responder agent that copies the authors writing style
    and generates an email for them. I am {final_context_object['my_email']}. 
    Your task is to reply to this mail {final_context_object["mail_I_want_to_reply_to"]}
    The Person you have to reply to is {final_context_object["person_I_want_to_reply_to"]}
    The three recent emails sent by me to this person are {recent_emails}.
    My stylometric features(the verbs, adjectives and adverbs I use in decreasing order
    are {final_context_object['my_stylometric_features']}
    Your task is to generate a reply to the email by using my using my stylometric 
    features. Make sure to use the greetings and the tone, stylometric features that I use 
    to generate the reply using all the context given to you .
    Here is some extra information about how the reply should be generated {additional_context} .
    Do not add unnecessary commas or stylometric features that are not used by me.
    """

    # You would typically pass final_context_object to a language model here
    # For now, we return the context object as the response:
    print('final context object', final_context_object)
    print('additional_context', additional_context)
    print('number of recent mails found', len(recent_emails))
    print('Print additional context', additional_context)
    try:
        # 2. Call the API to generate the CSV content
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        generated_email = response.text.strip()
        print(generated_email)
        return generated_email
    except Exception as e:
        print(f"An error occurred during content generation: {e}")

def extract_email(header_value):
    """
    Input: 'Aaryan Bhandari <bhandariaaryan16@gmail.com>'
    Output: 'bhandariaaryan16@gmail.com'
    """
    if not header_value:
        return ""
    # parseaddr returns a tuple: ('Real Name', 'email@address.com')
    # We only want the second part [1]
    name, email_address = parseaddr(header_value)
    return email_address

async def parse_eml_upload(file: UploadFile):
    """
    Reads an uploaded .eml file and returns a dictionary ready for the database.
    """
    # Read file content as bytes
    file_content = await file.read()
    
    # Use BytesParser with default policy to handle standard email quirks automatically
    msg = BytesParser(policy=policy.default).parsebytes(file_content)
    
    # 1. Basic Headers
    subject = msg.get('subject', '')
    sender_raw = msg.get('from', '')
    sender = extract_email(sender_raw)
    
    receiver_raw = msg.get('to', '')
    receiver = extract_email(receiver_raw)
    msg_id = msg.get('message-id', '').strip()
    
    # 2. Threading Headers
    in_reply_to = msg.get('in-reply-to', None)
    if in_reply_to:
        in_reply_to = in_reply_to.strip()
        
    # Handle References (Convert string to list for JSON column)
    # Header looks like: "<id1> <id2> <id3>"
    references_raw = msg.get('references', '')
    references_list = references_raw.split() if references_raw else []
    
    # 3. Date Parsing (Critical for sorting)
    date_str = msg.get('date')
    sent_at = None
    if date_str:
        try:
            sent_at = parsedate_to_datetime(date_str)
        except Exception:
            # Fallback if date is malformed
            sent_at = datetime.now()
    
    # 4. Body Extraction (Prefer Plain Text, fall back to HTML)
    content = ""
    body = msg.get_body(preferencelist=('plain', 'html'))
    if body:
        try:
            content = body.get_content()
        except Exception:
            content = "[Could not decode content]"
    
    return {
        "message_id": msg_id,
        "parent_message_id": in_reply_to,
        "references": references_list,
        "sender": sender,
        "receiver": receiver,
        "subject": subject,
        "content": content,
        "sent_at": sent_at,
    }

def get_emails_from_references(ref_list):
    """
    Given a list of message-id references (strings),
    return all EmailDB rows whose message_id matches any item in ref_list.
    Also print:
    - If the reference list is empty   
    - Number of emails found
    """
    # 1. Check if reference list is empty
    if not ref_list:
        print("No references provided.")
        return []

    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # 2. Query emails that match the references
        emails = (
            db.query(EmailDB)
            .filter(EmailDB.message_id.in_(ref_list))
            .all()
        )

        # 3. Print number of emails found
        print(f"Found {len(emails)} email(s) matching these references.")

        return emails

    finally:
        db_gen.close()


@app.post("/api/upload-eml")
async def upload_eml(
    context: str = Form(...),
    query: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):    
    """
    Upload an .eml file and parse it into an EmailDB object
    """
    # Validate file type
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="File must be a .eml file")
    
    try:
        # Parse the uploaded .eml file
        email_data = await parse_eml_upload(file)
        
        
        # Create EmailDB object using the parsed data
        email_db = EmailDB(
            message_id=email_data["message_id"],
            parent_message_id=email_data["parent_message_id"],
            references=email_data["references"],
            sender=email_data["sender"],
            receiver=email_data["receiver"],
            content=email_data["content"],
            subject=email_data["subject"],
            sent_at=email_data["sent_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process email: {str(e)}")
    
    email_store = EmailEmbeddingStore()
    semantically_similar_emails = email_store.search_similar_emails(query=query, n_results=3, sender_filter=email_db.receiver)
    complete_email_thread = get_emails_from_references(email_db.references)    
    historical_context, recent_emails = get_historical_content(
        db, 
        sender=email_db.sender, 
        receiver=email_db.receiver
    )
    features = extract_top_words(historical_context)
    
    # 3. Compile all information into a final context object for the next step passing to the  
    additional_context = context
    
    final_context_object = {
        "person_I_want_to_reply_to": email_db.sender,
        "my_email": email_db.receiver,
        "my_stylometric_features": features,
        "mail_I_want_to_reply_to": email_db.content,
    }

   
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing client. Check your API key. Error: {e}")
        return
    
    prompt = f"""
    You are an email-responder agent that copies the authors writing style
    and generates an email for them. I am {final_context_object['my_email']}. 
    Your task is to reply to this mail {final_context_object["mail_I_want_to_reply_to"]}
    The Person you have to reply to is {final_context_object["person_I_want_to_reply_to"]}
    The three recent emails sent by me to this person are {recent_emails}.
    My stylometric features(the verbs, adjectives and adverbs I use in decreasing order
    are {final_context_object['my_stylometric_features']}
    Your task is to generate a reply to the email by using my using my stylometric 
    features. Make sure to use the greetings and the tone, stylometric features that I use 
    to generate the reply using all the context given to you .
    I have also provided you these emails for additional stylometric features {semantically_similar_emails} .
    Here is some extra information about how the reply should be generated {additional_context} .
    Do not add unnecessary commas or stylometric features that are not used by me.
    Here is the complete email thread of the current conversation, it may also be 
    empty {complete_email_thread}
    """

    # You would typically pass final_context_object to a language model here
    # For now, we return the context object as the response:
    print('final context object', final_context_object)
    print('additional_context', additional_context)
    print('number of recent mails found', len(recent_emails))
    print('Print additional context', additional_context)
    print('Number of Semantically similar emails found', len(semantically_similar_emails))
    try:
        # 2. Call the API to generate the CSV content
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        generated_email = response.text.strip()
        print(generated_email)
        return generated_email
    except Exception as e:
        print(f"An error occurred during content generation: {e}")

        
