from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class TranslationAnnotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    input_text = db.Column(db.String(500), nullable=False)
    translation_text = db.Column(db.String(500), nullable=False)
    fluency = db.Column(db.Integer, nullable=False)
    adequacy = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key ke tabel User
    completed = db.Column(db.Boolean, default=False)  # Status anotasi

    user = db.relationship('User', backref='annotations')  # Relasi dengan User

    def __repr__(self):
        return f'<TranslationAnnotation {self.id}>'

    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    lastjob = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(100), nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # Tambahkan kolom role

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.id}>'
    
    