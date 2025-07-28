from database import engine, Base
from models import User, Message, Room

def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()  # Run table creation
    print("Tables Created Successfully")
