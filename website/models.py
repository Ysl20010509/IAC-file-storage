from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    data = db.Column(db.LargeBinary)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))

class Folder(db.Model):
    __tablename__ = "folder"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(400))
    foldername = db.Column(db.String(200))
    parent_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    itar = db.Column(db.Boolean, default=False)

    file = db.relationship('Upload')
    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    role = db.Column(db.String(50)) #user, admin
    itar_permission = db.Column(db.Boolean, default=False)
    upload = db.relationship('Upload')
    folder = db.relationship('Folder')
    