from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .database import get_db, Base, engine
from . import models # schemas are Pydantic models for request/response
from .schemas import EmailCreate, Generate
from .pos_tagging import extract_top_words
from typing import Tuple,List
from .models import EmailDB
import os
from google import genai

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

    
@app.post("/api/add-email")
def create_email_template(email: EmailCreate, db: Session = Depends(get_db)):
    # Create a new database object
    db_email = models.EmailDB(
        sender=email.sender, 
        receiver=email.receiver, 
        content=email.content
    )
    
    # Add, commit, and refresh to get the ID
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    
    return db_email

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
    You are an email-responderu agent that copies the authors writing style
    and generates an email for them. I am {final_context_object['my_email']}. 
    Your task is to reply to this mail {final_context_object["mail_I_want_to_reply_to"]}
    The Person you have to reply to is {final_context_object["person_I_want_to_reply_to"]}
    The three recent emails sent by me to this person are {recent_emails}.
    My stylometric features(the verbs, adjectives and adverbs I use in decreasing order)
    are {final_context_object['my_stylometric_features']}
    Your task is to generate a reply to the email by 
    Make sure to use the greetings from the list of recents emails along with that.
    Here is some extra information  {additional_context}
    Generate a reply keeping in mind the person's stylometric features.
    Do not add unnecessary commas.
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
