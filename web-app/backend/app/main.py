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
email_embedding_store = EmailEmbeddingStore()

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
                print(f"ChromaDB Error for message_id {new_email.message_id}: {e}")
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
            and_(EmailDB.sender == receiver, EmailDB.receiver == sender),
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


@app.get("/emails/thread/{subject:path}")
async def get_thread_by_subject(
    subject: str,
    db: Session = Depends(get_db)
):
    """
    Get all emails in a thread by subject (includes Re: variations).
    Returns emails in chronological order.
    """
    # Strip "Re: " prefix to get base subject
    base_subject = subject.strip()
    if base_subject.lower().startswith("re:"):
        base_subject = base_subject[3:].strip()
    
    # Match all emails with this subject regardless of sender/receiver
    emails = db.query(EmailDB).filter(
        or_(
            EmailDB.subject == base_subject,
            EmailDB.subject.ilike(f"Re: {base_subject}"),
            EmailDB.subject.ilike(f"Re:{base_subject}"),
        )
    ).order_by(EmailDB.sent_at.asc()).all()
    
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
def summarize_thread_context(thread_context: str) -> str:
    """
    Takes thread context and summarizes it using Gemini.
    
    Args:
        thread_context: Formatted string containing all thread messages
        
    Returns:
        A concise summary of the thread conversation
    """
    
    if not thread_context or thread_context.strip() == "":
        return "No thread context to summarize."
    
    print("\n" + "=" * 60)
    print("DEBUG: summarize_thread_context() CALLED")
    print("=" * 60)
    print(f"Thread context length: {len(thread_context)} characters")
    print("-" * 60)
    
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return "Error: Could not initialize Gemini client."
    
    summary_prompt = f"""
    You are a precise email thread summarizer. Analyze the following email thread and provide a concise summary.

    === EMAIL THREAD ===
    {thread_context}

    === INSTRUCTIONS ===
    Provide a summary that includes:
    1. **Main Topic**: What is this thread about? (1 sentence)
    2. **Key Points**: What are the main points discussed? (bullet points)
    3. **Current Status**: Where does the conversation stand? What was the last message about?
    4. **Action Items**: Any pending tasks, questions, or requests that need addressing?
    5. **Participants**: Who is involved and what are their roles/positions in this conversation?

    Keep the summary concise but informative. Focus on what's most relevant for crafting a reply. Should be no longer than 50 words.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=summary_prompt,
        )
        summary = response.text.strip()
        
        print("THREAD SUMMARY GENERATED:")
        print("-" * 40)
        print(summary)
        print("=" * 60 + "\n")
        
        return summary
        
    except Exception as e:
        print(f"Error during summarization: {e}")
        return f"Error summarizing thread: {str(e)}"
    
def get_historical_content(db: Session, sender: str, receiver: str) -> Tuple[str, List[str]]:
    """
    Retrieves and concatenates all 'content' from emails where the 
    original 'receiver' sent the email to the original 'sender'.
    Also fetches the content of the 3 most recent emails in that conversation.
    
    Condition: EmailDB.sender == receiver AND EmailDB.receiver == sender (for all emails)
    
    Returns: A tuple (concatenated_content, recent_emails_content_list)
    """
    
    print("\n" + "=" * 60)
    print("DEBUG: get_historical_content() CALLED")
    print("=" * 60)
    print(f"Input sender: {sender}")
    print(f"Input receiver: {receiver}")
    print("-" * 60)
    
    # 1. Define the specific filter condition for the Receiver -> Sender direction
    filter_condition = (EmailDB.sender == sender) & (EmailDB.receiver == receiver)
    
    print(f"Filter: EmailDB.sender == '{sender}' AND EmailDB.receiver == '{receiver}'")
    print("-" * 60)
    
    # --- Fetch ALL matching content for concatenation ---
    historical_emails_all = db.query(EmailDB.content).filter(
        filter_condition
    ).limit(100).all()
    
    print(f"Total emails found (limit 100): {len(historical_emails_all)}")
    print("-" * 60)
    
    # Extract and concatenate content
    content_list_all = [c[0] for c in historical_emails_all]
    concatenated_content = "\n\n---\n\n".join(content_list_all)

    print("ALL EMAILS CONTENT PREVIEW:")
    print("-" * 40)
    for i, content in enumerate(content_list_all, 1):
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"[Email {i}]: {preview}")
    print("-" * 60)

    # --- Fetch the 3 MOST RECENT email contents ---
    # We apply the same filter, but order by timestamp descending and limit to 3.
    historical_emails_recent = db.query(EmailDB.content).filter(
        filter_condition
    ).order_by(
        EmailDB.sent_at.desc() # Assumes a 'timestamp' column exists
    ).limit(3).all()

    # Extract the content for the recent emails
    recent_emails_content_list = [c[0] for c in historical_emails_recent]

    print(f"Recent emails found (limit 3): {len(recent_emails_content_list)}")
    print("-" * 40)
    print("RECENT EMAILS CONTENT:")
    print("-" * 40)
    for i, content in enumerate(recent_emails_content_list, 1):
        preview = content[:150] + "..." if len(content) > 150 else content
        print(f"[Recent {i}]:")
        print(preview)
        print("-" * 40)
    
    print("=" * 60)
    print(f"SUMMARY: Returning {len(concatenated_content)} chars concatenated, {len(recent_emails_content_list)} recent emails")
    print("=" * 60 + "\n")

    # Return both the concatenated string and the list of recent email content
    return concatenated_content, recent_emails_content_list



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
    thread_messages = data.thread_messages
    
    # 2. Use the database function to retrieve concatenated historical content
    historical_context, recent_emails = get_historical_content(
        db, 
        sender=clean_sender, 
        receiver=clean_receiver
    )
    features = extract_top_words(historical_context)
    
    # 3. Format thread messages for context
    thread_context = ""
    if thread_messages:
        thread_context = "\n\n--- THREAD HISTORY (in chronological order) ---\n"
        for i, msg in enumerate(thread_messages, 1):
            thread_context += f"\n[Message {i}]\n"
            thread_context += f"From: {msg.sender}\n"
            thread_context += f"To: {msg.receiver}\n"
            thread_context += f"Date: {msg.sent_at or 'Unknown'}\n"
            thread_context += f"Subject: {msg.subject}\n"
            thread_context += f"Content:\n{msg.content}\n"
            thread_context += "-" * 40
    
    # 4. Summarize thread context
    thread_summary = summarize_thread_context(thread_context)
    
    # 5. Semantic search for similar emails based on thread context and mail to reply to
    search_query = f"{data.content} {thread_summary}"
    
    email_embedding_store = EmailEmbeddingStore()
    
    # Search for similar emails sent BY ME (clean_receiver is my email in this context)
    similar_emails = email_embedding_store.search_similar_emails(
        query=search_query,
        n_results=3,
        sender_filter=clean_sender  
    )
    
    # Format similar emails for the prompt
    similar_emails_context = ""
    if similar_emails:
        similar_emails_context = "\n\n--- SEMANTICALLY SIMILAR EMAILS I'VE SENT ---\n"
        for i, email in enumerate(similar_emails, 1):
            similar_emails_context += f"\n[Similar Email {i}] (Similarity distance: {email['distance']:.4f})\n"
            similar_emails_context += f"Content:\n{email['content']}\n"
            similar_emails_context += "-" * 40
    
    print("\n" + "=" * 60)
    print("DEBUG: SEMANTIC SEARCH RESULTS")
    print("=" * 60)
    print(f"Search query (truncated): {search_query[:200]}...")
    print(f"Number of similar emails found: {len(similar_emails)}")
    for i, email in enumerate(similar_emails, 1):
        print(f"[{i}] Distance: {email['distance']:.4f} | Preview: {email['content'][:100]}...")
    print("=" * 60 + "\n")
    
    # 6. Compile all information into a final context object
    additional_context = custom_prompt
    
    final_context_object = {
        "person_I_want_to_reply_to": clean_sender,
        "my_email": clean_receiver,
        "my_stylometric_features": features,
        "mail_I_want_to_reply_to": data.content,
        "thread_summary": thread_summary,
        "similar_emails_context": similar_emails_context,
    }
    
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing client. Check your API key. Error: {e}")
        return
    
    prompt = f"""
    You are an expert email style transfer agent. Your task is to generate a reply email that perfectly mimics the writing style of a specific person.

    === IDENTITY ===
    I am: {final_context_object['my_email']}
    Replying to: {final_context_object['person_I_want_to_reply_to']}

    === EMAIL TO REPLY TO ===
    {final_context_object["mail_I_want_to_reply_to"]}

    === THREAD SUMMARY ===
    {final_context_object['thread_summary']}

    === MY RECENT EMAILS TO THIS PERSON (study these for style) ===
    {recent_emails}

    === SEMANTICALLY SIMILAR EMAILS I'VE WRITTEN (study these for relevant content & style) ===
    These are emails I've written in the past that are topically similar to the current conversation.
    Use these to understand how I typically write about similar topics:
    {final_context_object['similar_emails_context']}

    === MY STYLOMETRIC FEATURES ===
    Top verbs, adjectives, and adverbs I frequently use (in decreasing order of frequency):
    {final_context_object['my_stylometric_features']}

    === STYLE TRANSFER INSTRUCTIONS ===
    Analyze my recent emails and semantically similar emails above, then copy these specific style features:
    
    1. **Sentence Structure**: Match my typical sentence length and complexity. Do I use short punchy sentences or longer flowing ones? Do I prefer simple sentences or compound/complex structures with multiple clauses?
    2. **Vocabulary Choice**: Use words at the same sophistication level as mine. Am I formal or informal? Do I use technical jargon or casual language? Copy my word choices.
    3. **Tone**: Match my tone exactly - whether professional, friendly, authoritative, casual, urgent, warm, or direct. Maintain the same emotional register.
    4. **Formality Level**: Copy my greeting style e.g. (Hi/Hello/Dear/Hey), my closing style e.g. (Bests/Thanks/Regards/Cheers), my use of politeness markers, and whether I use contractions (don't vs do not).
    5. **Punctuation Patterns**: Match my punctuation habits - do I use exclamation marks? Dashes? Semicolons? Ellipses? How frequently?
    6. **Paragraph Organization**: Structure paragraphs like I do - match my typical paragraph length and how I organize information.
    7. **Expressiveness**: Match my level of expressiveness - do I use many adjectives and adverbs? Do I use intensifiers (very, really, extremely) or hedging language (perhaps, maybe, I think)?
    8. **Voice**: Match my preference for active or passive voice.

    === ADDITIONAL CONTEXT FOR THIS REPLY ===
    {additional_context}

    === CRITICAL RULES ===
    - Match my greeting and sign-off patterns exactly
    - Use the semantically similar emails to understand how I discuss similar topics
    - The reply should address the content of the email while matching my style

    Generate ONLY the email reply, nothing else. No explanations or meta-commentary.
    """
    
    print('final context object', final_context_object)
    print('additional_context', additional_context)
    print('number of recent mails found', len(recent_emails))
    print('number of thread messages', len(thread_messages))
    print('number of similar emails found', len(similar_emails))
    
    try:
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

        
