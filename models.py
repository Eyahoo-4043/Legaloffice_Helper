from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UserSetting(db.Model):
    """User settings model to store API keys"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    api_key = db.Column(db.String(100), nullable=False)
    default_assembly_term = db.Column(db.String(10), nullable=False, default="22")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)