from datetime import datetime
from app import db

class Download(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    url = db.Column(db.String(512), nullable=False)
    title = db.Column(db.String(512))
    format_id = db.Column(db.String(32))
    status = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    file_path = db.Column(db.String(512))
    file_size = db.Column(db.BigInteger)
