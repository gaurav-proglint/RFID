from sqlalchemy import Column,Integer,String,ForeignKey
from sqlalchemy.orm import relationship
from config import Base

class RFID(Base):
    __tablename__='RFID'
    id=Column(String,primary_key=True)
    rfid=Column(String)
    record_creation_time=Column(String)

class AUDIT(Base):
    __tablename__='AUDIT'
    audit_id=Column(String,primary_key=True)
    fid=Column(String,ForeignKey(RFID.id))
    rfid_unique_id=Column(String)
    rfid_ipadress=Column(String)    
    location=Column(String)
    details=Column(String)
    external_api_url=Column(String)
    record_creation_time=Column(String)
    parent = relationship('RFID')