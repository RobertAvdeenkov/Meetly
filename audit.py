from models import AutLog
from database import SessionLocal

def log_action(user_id,entity,details=''):
    db = SessionLocal()
    try:
        log = AutLog(
            user_id=user_id,
            entity=entity,
            info=details
        )
        db.add(log)
        db.commit()
    except Exception as e:
        print("ERROR:",e)
        db.rollback()
    finally:
        db.close()