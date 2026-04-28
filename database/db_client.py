from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from shared.config import config

class DatabaseClient:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    # Trả về một session để giao tiếp với DB
    def get_session(self):
        return self.SessionLocal()

db_client = DatabaseClient()
