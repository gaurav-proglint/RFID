from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from sqlalchemy.ext.declarative import declarative_base
load_dotenv() 
user=os.getenv("user")
password=os.getenv("password")
host=os.getenv("host")
port=os.getenv("port")
database=os.getenv("database")

database_url=f'postgresql://{user}:{password}@{host}:{port}/{database}'
engine=create_engine(database_url)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base=declarative_base()
def get_db():
    db=SessionLocal()
    return db