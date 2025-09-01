from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    premium_expiry = db.Column(db.DateTime, nullable=True)
    
    entries = db.relationship('JournalEntry', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_premium_active(self):
        if not self.is_premium:
            return False
        if self.premium_expiry and self.premium_expiry < datetime.utcnow():
            self.is_premium = False
            self.premium_expiry = None
            db.session.commit()
            return False
        return True

class JournalEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Store AI+typed mood scores
    mood_scores = db.Column(db.JSON, nullable=False)
    
    # Store typed mood (overrides AI if user explicitly typed an emotion)
    typed_mood = db.Column(db.String(20), nullable=True)
