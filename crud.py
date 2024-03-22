from sqlalchemy.orm import session
import models
import uuid
import datetime
id = uuid.uuid1() 
current_time = datetime.datetime.now()

def insert_rfid(db:session,rfid:str):
    new_record=models.RFID(id=str(id),rfid=rfid,record_creation_time=current_time)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

def search_rfid(db:session,rfid:str):
    return db.query(models.RFID).filter(models.RFID.rfid==rfid).first()

def insert_audit(db:session,fid:str,rfid_unique_id:str,rfid_ipadress:str,location:str,details:str,external_api_url:str):
    new_record=models.AUDIT(
                            audit_id=str(id),
                            fid=fid,
                            rfid_unique_id=rfid_unique_id,
                            rfid_ipadress=rfid_ipadress,
                            location=location,
                            details=details,
                            external_api_url=external_api_url,
                            record_creation_time=current_time
                            )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
                        