import os
from flask import Flask
from models import db

# Create the Flask app
app = Flask(__name__)

# Configure secret key
app.secret_key = os.environ.get("SESSION_SECRET", "법규제도실_helper_secret_key")

# Configure database
# Ensure database URL is properly set
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # Rewrite postgres:// to postgresql:// (required for SQLAlchemy)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Fallback to SQLite if database URL is not available
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///legaloffice.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Import routes after app is created to avoid circular imports
from app import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
