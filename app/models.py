from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Define roles
    ROLES = {
        'administrator': ['admin', 'analyst', 'viewer'],
        'developer': ['analyst', 'viewer'],
        'customer': ['viewer'],
    }
    
    def has_permission(self, required_role):
        return required_role in self.ROLES.get(self.role, [])

    @property
    def is_admin(self):
        return self.role == 'administrator'
    

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.String(20), nullable=False)
    product_service_category = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    feedback_length = db.Column(db.Integer, nullable=False)  # New column for length of feedback text
    sentiment_category = db.Column(db.String(20), nullable=False)  # Renamed sentiment category
    sentiment_numeric = db.Column(db.Integer, nullable=False)  # Numeric sentiment score

    def __repr__(self):
        return f"<Feedback {self.id} - {self.feedback_text[:20]}>"


