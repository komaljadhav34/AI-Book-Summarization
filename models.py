from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='user')  # 'admin' or 'user'
    
    books = db.relationship('Book', backref='owner', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    raw_text = db.Column(db.Text, nullable=False)
    chunks = db.Column(db.Text)
    summary = db.Column(db.Text)
    
    # Learning features
    mindmap = db.Column(db.Text)
    quizzes = db.Column(db.Text)
    
    # Background processing fields
    processing_status = db.Column(db.String(20), default='none')  # none, processing, completed, error
    processing_started_at = db.Column(db.Float)
    total_words = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
