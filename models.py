from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    resumes = db.relationship('Resume', backref='owner', lazy=True)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    role_applied = db.Column(db.String(100), nullable=False)
    analysis_data = db.Column(db.Text, nullable=True) # JSON string of analysis
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SMTPConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String(150), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    use_tls = db.Column(db.Boolean, default=True)
