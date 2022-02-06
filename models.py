from flask_sqlalchemy import SQLAlchemy
 
db = SQLAlchemy()

class Users(db.Model):

    userid = db.Column(db.String(), primary_key=True)
    displayname = db.Column(db.String())
    pictureurl = db.Column(db.String())
    trash  = db.Column(db.String())
    timestamp = db.Column(db.String())