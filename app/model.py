from passlib.hash import pbkdf2_sha256 as sha256
from flask_sqlalchemy import SQLAlchemy

from AppContext import AppContext
db = AppContext().db

class UserModel(db.Model):
    __tablename__ = 'users'

    # user fields - http://flask-sqlalchemy.pocoo.org/2.3/models/
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password = db.Column(db.String(120), nullable = False)
    balance = db.Column(db.Float, nullable = False, default='0')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    # queries on the DB model
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username = username).first()

    @classmethod
    def transact(cls, source_user, amount, target_user):
        source_user.balance -= amount
        target_user.balance += amount
        db.session.commit()

    # static methods (unrelated to DB model)
    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)
