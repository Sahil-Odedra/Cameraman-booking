from flask import Flask, render_template, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import config
from flask import request
import os
from datetime import datetime
from models import db, User, Cameraman, Booking
from flask import flash, redirect, url_for, session, request
from werkzeug.utils import secure_filename
from flask_mail import Mail,Message

app = Flask(__name__)
app.config.from_object(config)
mail=Mail(app)
app.secret_key = 'cameramanbooking123'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['images'] = os.path.join(BASE_DIR, 'static', 'images')
os.makedirs(app.config['images'], exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS

db.init_app(app)


@app.route('/home')
def home_user():
    if 'user_mobile' not in session:
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('login_user'))

    search_city = request.args.get('city')
    max_price = request.args.get('price_max', type=int)
    search_date = request.args.get('date')

    query = Cameraman.query

    if search_city:
        query = query.filter(Cameraman.city.ilike(f'%{search_city}%'))
    if max_price:
        query = query.filter(Cameraman.price <= max_price)
    if search_date:
        try:
            booking_date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
            
            booked_cameramen_subquery = db.session.query(Booking.cameraman_mobile).filter(Booking.booking_date == booking_date_obj, Booking.status == 'confirmed').subquery()
            
            query = query.filter(Cameraman.mobile.notin_(booked_cameramen_subquery))
        except ValueError:
            flash('Invalid date format provided. Please use YYYY-MM-DD.', 'error')
            pass

    filtered_cameramen = query.all()
    
    search_values = {'city': search_city, 'price_max': max_price, 'date': search_date}

    return render_template('home.html', cameramen=filtered_cameramen, search_values=search_values)


@app.route('/view_cameraman_profile/<mobile>')
def view_cameraman_profile(mobile):
    if 'user_mobile' not in session:
        flash('Please log in to view profiles.', 'error')
        return redirect(url_for('login_user'))

    cameraman = Cameraman.query.get_or_404(mobile)

    return render_template('view_cameraman_profile.html', cameraman=cameraman)


@app.route("/register_user",methods=['POST','GET'])
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        mobile=request.form['mobile']
        city=request.form['city']
        password=request.form['password']
        confirm_password=request.form['confirm_password']
        if password != confirm_password:
            return "Passwords do not match. Please try again."
        if User.query.get(mobile):
            return "Mobile Number already registred."

        new_user=User(name=name, mobile=mobile, password=password, city=city)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login_user'))
    return render_template('user_register.html')


@app.route('/book/<string:cameraman_mobile>', methods=['GET', 'POST'])
def book_cameraman(cameraman_mobile):
    if 'user_mobile' not in session:
        flash('You must be logged in to book a cameraman.', 'error')
        return redirect(url_for('login_user'))

    cameraman = Cameraman.query.get_or_404(cameraman_mobile)

    if request.method == 'POST':
        booking_date_str = request.form.get('booking_date')
        
        if not booking_date_str:
            flash('Please select a date for the booking.', 'error')
            return redirect(url_for('book_cameraman', cameraman_mobile=cameraman.mobile))

        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()

        # this is to avoid dublicates
        existing_booking = Booking.query.filter_by(cameraman_mobile=cameraman_mobile,
            booking_date=booking_date).first()
        if existing_booking:
            flash("Not Available on this date","error")
            return redirect(url_for('book_cameraman',cameraman_mobile=cameraman_mobile))
        new_booking = Booking(user_mobile=session['user_mobile'],cameraman_mobile=cameraman.mobile,
        booking_date=booking_date, price=cameraman.price, status='pending')

        db.session.add(new_booking)
        db.session.commit()

        #for sending mail
        try:
            user = User.query.get(session['user_mobile'])
            msg=Message(subject="New Booking request",
                    recipients=[cameraman.email],
                    body=f'''
                    Hello {cameraman.name}

                    you have a new booking request from {user.name}
                    Please login to accept or reject the request.

                    Regards...
                    ''')
            mail.send(msg)
        except:
            flash("Unable to send Mail to the Cameraman, But your booking was successfull.")

        flash(f'Your booking request for {cameraman.name} has been sent!', 'success')
        return redirect(url_for('home_user'))
   
    return render_template('book_cameraman.html', cameraman=cameraman)


@app.route('/cameraman/update_cameraman', methods=['GET', 'POST'])
def update_cameraman():
    if 'cameraman_mobile' not in session:
        flash("You must be logged in to edit your profile.", "error")
        return redirect(url_for('login_cameraman'))

    mobile = session['cameraman_mobile']
    cameraman = Cameraman.query.get_or_404(mobile)

    if request.method == 'POST':
        cameraman.name = request.form['name']
        cameraman.email = request.form['email']
        cameraman.city = request.form['city']
        cameraman.exp = int(request.form['exp'])
        cameraman.price = int(request.form['price'])
        cameraman.description = request.form['description']
        
        new_password=request.form.get('new_password')
        confirm_password=request.form.get('confirm_password')
        if new_password:
            if confirm_password != new_password:
                flash("Both the passwords do not match.","error")
                return redirect(url_for('update_cameraman'))
            cameraman.password=new_password
            flash("Password updated Successfully","success")

        file = request.files.get('portfolio_img')
        if file and file.filename:
            filename = secure_filename(cameraman.mobile + "_" + file.filename)
            file.save(os.path.join(app.config['images'], filename))
            cameraman.portfolio_img = filename

        db.session.commit()

        flash("Your profile has been updated successfully!", "success")
        return redirect(url_for('profile_cameraman',mobile=cameraman.mobile))

    return render_template('update_cameraman.html', cameraman=cameraman)


@app.route('/cameraman/bookings')
def manage_bookings():
    if 'cameraman_mobile' not in session:
        flash("You must be logged in to manage bookings.", "error")
        return redirect(url_for('login_cameraman'))
    mobile = session['cameraman_mobile']
    
    cameraman_bookings = db.session.query(Booking, User).join(
        User, Booking.user_mobile == User.mobile
    ).filter(Booking.cameraman_mobile == mobile).all()

    return render_template('manage_bookings.html', bookings=cameraman_bookings)


@app.route('/booking/accept/<int:booking_id>', methods=['POST'])
def accept_booking(booking_id):
    if 'cameraman_mobile' not in session:
        flash("You are not authorized to perform this action.", "error")
        return redirect(url_for('login_cameraman'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.cameraman_mobile != session['cameraman_mobile']:
        flash("You do not have permission to modify this booking.", "error")
        return redirect(url_for('manage_bookings'))

    booking.status = 'Accepted'
    db.session.commit()

    flash("Booking has been successfully accepted!", "success")
    return redirect(url_for('manage_bookings'))


@app.route('/booking/reject/<int:booking_id>', methods=['POST'])
def reject_booking(booking_id):
    if 'cameraman_mobile' not in session:
        flash("You are not authorized to perform this action.", "error")
        return redirect(url_for('login_cameraman'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.cameraman_mobile != session['cameraman_mobile']:
        flash("You do not have permission to modify this booking.", "error")
        return redirect(url_for('manage_bookings'))

    booking.status = 'Rejected'
    db.session.commit()

    flash("Booking has been successfully Rejected!", "success")
    return redirect(url_for('manage_bookings'))


@app.route('/my_bookings')
def my_bookings():
    if 'user_mobile' not in session:
        flash('You need to be logged in to view your bookings.', 'error')
        return redirect(url_for('login_user'))

    user_bookings = db.session.query(Booking, Cameraman).join(
        Cameraman, Booking.cameraman_mobile == Cameraman.mobile
    ).filter(Booking.user_mobile == session['user_mobile']).all()

    return render_template('my_bookings.html', bookings=user_bookings)


@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    error = None
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']
        user = User.query.get(mobile)
        if user and user.password == password:
            session['user_mobile'] = user.mobile
            return redirect(url_for('home_user'))
        else:
            error = "Invalid Credentials"
    return render_template('login_user.html', error=error)


@app.route('/cameraman_profile/<mobile>')
def profile_cameraman(mobile):
    if 'cameraman_mobile' not in session or session['cameraman_mobile'] != mobile:
        return redirect(url_for('login_cameraman'))

    cameraman = Cameraman.query.get(mobile)
    if not cameraman:
        return "No Such User found"
    return render_template('profile_cameraman.html', cameraman=cameraman)


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('cameraman_mobile', None)
    return redirect(url_for('login_cameraman'))


@app.route('/login_cameraman', methods=['GET', 'POST'])
def login_cameraman():
    error = None
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        cameraman = Cameraman.query.get(mobile)
        if cameraman and cameraman.password == password:
            session['cameraman_mobile'] = cameraman.mobile
            return redirect(url_for('profile_cameraman', mobile=cameraman.mobile))
        else:
            error = "Invalid Credential"
    return render_template('login_cameraman.html', error=error)


@app.route('/')
def home():
    return redirect(url_for('login_user'))


@app.route('/register_cameraman', methods=['GET', 'POST'])
def register_cameraman():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        city = request.form.get('city')
        exp = request.form.get('exp')
        price = request.form.get('price')
        description = request.form.get('description')

        if password != confirm_password:
            return "Passwords do not match. Please try again."

        file = request.files['portfolio_img']
        filename = None
        if file and file.filename != '':
            filename = secure_filename(mobile + "_" + file.filename)
            file.save(os.path.join(app.config['images'], filename))

        new_cameraman = Cameraman(name=name, email=email, mobile=mobile, password=password, city=city,
            exp=int(exp), price=price, description=description, portfolio_img=filename)
        
        db.session.add(new_cameraman)
        db.session.commit()

        return render_template('profile_cameraman.html', cameraman=new_cameraman)
    return render_template('register_cameraman.html')
   

if __name__ == "__main__":
    app.run(debug=True)