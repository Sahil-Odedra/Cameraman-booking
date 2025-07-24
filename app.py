from flask import Flask, render_template, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import config
from flask import request
import os
from datetime import datetime
from models import db, User, Cameraman, Booking
from flask import flash, redirect, url_for, session, request
from werkzeug.utils import secure_filename

app = Flask(__name__)
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
    search_price_max = request.args.get('price_max', type=int)
    search_date_str = request.args.get('date')

    query = Cameraman.query

    if search_city:
        query = query.filter(Cameraman.city.ilike(f'%{search_city}%'))

    if search_price_max:
        query = query.filter(Cameraman.price <= search_price_max)
        
    if search_date_str:
        try:
            # Convert the date string from the form into a Python date object
            booking_date_obj = datetime.strptime(search_date_str, '%Y-%m-%d').date()
            
            # This subquery creates a list of all cameraman IDs who are already booked
            # on the selected date with a 'confirmed' status.
            booked_cameramen_subquery = db.session.query(Booking.cameraman_id).filter(
                Booking.booking_date == booking_date_obj,
                Booking.status == 'confirmed'
            ).subquery()
            
            # This updates the main query to exclude any cameraman whose ID is in the "booked" list.
            query = query.filter(Cameraman.id.notin_(booked_cameramen_subquery))
        except ValueError:
            # This handles cases where the user enters an invalid date format.
            flash('Invalid date format provided. Please use YYYY-MM-DD.', 'error')
            pass

    # Step 4: Execute the final, filtered query to get the results
    filtered_cameramen = query.all()
    
    # This dictionary helps remember the user's search terms and repopulate the form
    search_values = {
        'city': search_city,
        'price_max': search_price_max,
        'date': search_date_str
    }

    # Step 5: Render the home.html template, passing the list of cameramen and the search values
    return render_template('home.html', cameramen=filtered_cameramen, search_values=search_values)


@app.route('/view_cameraman_profile/<mobile>')
def view_cameraman_profile(mobile):
    if 'user_mobile' not in session:
        flash('Please log in to view profiles.', 'error')
        return redirect(url_for('login_user'))

    # .get_or_404() will show a "Not Found" page if no cameraman with that mobile exists.
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

        return render_template('login_user.html')
    return render_template('user_register.html')


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
        mobile = request.form['mobile']
        password = request.form['password']
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
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        city = request.form['city']
        exp = request.form['exp']
        price = request.form['price']
        description = request.form['description']

        if password != confirm_password:
            return "Passwords do not match. Please try again."

        # File handling
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