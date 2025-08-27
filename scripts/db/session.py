from sqlalchemy.orm import Session
from scripts.db.s3_backup import backup_to_s3
import logging
import atexit
import os

logger = logging.getLogger(__name__)
_backup_needed = False
_is_lambda = bool(os.getenv('AWS_LAMBDA_FUNCTION_NAME'))

class BatchBackupSession(Session):
    def commit(self):
        global _backup_needed
        super().commit()
        if _is_lambda:
            _backup_needed = True

def _backup_on_exit():
    global _backup_needed
    if _backup_needed and _is_lambda:
        try:
            backup_to_s3()
            logger.info("Batch backup completed")
        except Exception as e:
            logger.warning(f"Batch backup failed: {e}")
        _backup_needed = False

# Register backup to run at Lambda exit (only in Lambda)
if _is_lambda:
    atexit.register(_backup_on_exit)

def get_db_with_backup():
    from scripts.db.database import SessionLocal, engine
    db = BatchBackupSession(bind=engine)
    try:
        yield db
    finally:
        db.close()