import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'AI-News')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from shared.config import config

class DatabaseClient:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self):
        """Trả về một session để giao tiếp với DB"""
        return self.SessionLocal()

db_client = DatabaseClient()
