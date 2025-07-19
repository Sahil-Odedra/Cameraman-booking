from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()

class User(db.Model):
    __tablename__='users'
    mobile=db.Column(db.String(10),primary_key=True)
    password=db.Column(db.String(50),nullable=False)
    name=db.Column(db.String(50),nullable=False)
    city=db.Column(db.String(50),nullable=False)
class Cameraman(db.Model):
    __tablename__ = 'cameraman'

    mobile = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email=db.Column(db.String(50),nullable=False)
    city = db.Column(db.String(100), nullable=False)
    exp = db.Column(db.Integer, nullable=False)
    price = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    portfolio_img = db.Column(db.String(255), nullable=True)

class Booking(db.Model):
    __tablename__='bookings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_mobile = db.Column(db.String(10), db.ForeignKey('users.mobile', ondelete='CASCADE'), nullable=False)
    cameraman_mobile = db.Column(db.String(10), db.ForeignKey('cameraman.mobile', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')