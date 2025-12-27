from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. SQLAlchemy Database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///experiments/.eml.db"

# 2. Database Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Session Maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Declarative Base
Base = declarative_base()

# 5. Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_database_tables():
    """
    Creates the database file (if it doesn't exist) and all tables 
    defined by classes inheriting from Base.
    """
    print(f"Attempting to create tables in: {SQLALCHEMY_DATABASE_URL}")
    
    # This command checks all classes inheriting from Base (like EmailDB)
    # and generates the necessary CREATE TABLE statements for the database
    # connected to by the 'engine'.
    Base.metadata.create_all(bind=engine)
    
    print(" Database file and 'email_templates' table created successfully.")


        