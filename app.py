from flask import Flask, render_template, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
import config
from flask import request
import os
from models import db,User,Cameraman,Booking
from werkzeug.utils import secure_filename

app=Flask(__name__)

app.config['images'] = 'static/images'
app.config["SQLALCHEMY_DATABASE_URI"]=config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=config.SQLALCHEMY_TRACK_MODIFICATIONS
os.makedirs(app.config['images'], exist_ok=True)

db.init_app(app)

@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    error=None
    if request.method == 'POST':
        mobile = request.form['mobile']
        password=request.form['password']
        user = User.query.get(mobile)
        if user and user.password == password:
            session['user_mobile'] = user.mobile
            return "Welcome " + user.name
        else:
            error = "Invalid Credentials"
    return render_template('login_user.html', error=error)

@app.route('/cameraman_profile/<mobile>')
def profile_cameraman(mobile):
    if 'cameraman_mobile' not in session or session['cameraman_mobile']!=mobile:
        return redirect(url_for('login_cameraman'))

    cameraman=Cameraman.query.get(mobile)
    if not cameraman:
        return "No Such User found"
    return render_template('profile_cameraman.html',cameraman=cameraman)

@app.route('/logout')
def logout():
    session.pop('cameraman_mobile',None)
    return redirect(url_for('login_cameraman'))

@app.route('/login_cameraman', methods=['GET','POST'])
def login_cameraman():
    error=None
    if request.method=='POST':
        mobile=request.form['mobile']
        password=request.form['password']
        cameraman=Cameraman.query.get(mobile)
        if cameraman and cameraman.password==password:
            session['cameraman_mobile']=cameraman.mobile
            return redirect(url_for('profile_cameraman',mobile=cameraman.mobile))
        else:
            error="Invalid Credential"
    return render_template('login_cameraman.html',error=error)

@app.route('/')
def home():
    return redirect(url_for('login_cameraman'))

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

        print("wow3")
        if password != confirm_password:
            return "Passwords do not match. Please try again."

        # File handling
        file = request.files['portfolio_img']
        filename = None
        if file and file.filename != '':
            filename = secure_filename(mobile + "_" + file.filename)
            file.save(os.path.join(app.config['images'], filename))

        new_cameraman = Cameraman(
            name=name,
            email=email,
            mobile=mobile,
            password=password,
            city=city,
            exp=int(exp),
            price=price,
            description=description,
            portfolio_img=filename
        )
        db.session.add(new_cameraman)
        db.session.commit()

        return render_template('profile_cameraman.html', cameraman=new_cameraman)

    return render_template('register_cameraman.html')

if __name__ == "__main__":
    app.run(debug=True)