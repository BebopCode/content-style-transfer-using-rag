from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import get_db
from .models import EmailDB

def get_highest_receiver():
    """
    Queries the database to find the receiver address that appears most frequently.
    
    Returns: A tuple (receiver_email, count) or None if the table is empty.
    """
    # 1. Get a database session
    db_generator = get_db()
    db: Session = next(db_generator) 
    
    try:
        # 2. Construct the query
        # - func.count(EmailDB.receiver): Counts the number of times each receiver appears.
        # - group_by(EmailDB.receiver): Groups the results by the receiver address.
        # - order_by(func.count(EmailDB.receiver).desc()): Sorts the groups by count, descending (highest first).
        # - limit(1): Takes only the top result.
        
        highest_receiver_result = db.query(
            EmailDB.receiver,
            func.count(EmailDB.receiver).label('count')
        ).group_by(EmailDB.receiver).order_by(func.count(EmailDB.receiver).desc()).limit(1).first()
        
        if highest_receiver_result:
            receiver_email, count = highest_receiver_result
            print(f" Highest Receiver: **{receiver_email}** (Count: {count})")
            return receiver_email, count
        else:
            print("No records found in the 'email_templates' table.")
            return None
            
    except Exception as e:
        print(f" An error occurred during the query: {e}")
        return None
    finally:
        # 3. Close the session
        db_generator.close()

if __name__ == "__main__":
    # Ensure your database setup and insertion script (if needed) are run first
    # Example call:
    highest_receiver = get_highest_receiver()
    print(highest_receiver)
    pass