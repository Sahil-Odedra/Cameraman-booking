db_user="root"
db_password=""
db_name="cameraman_booking"
db_host="localhost"

SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
SQLALCHEMY_TRACK_MODIFICATIONS=False

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'sahilodedra26@gmail.com'
MAIL_PASSWORD = 'mvzq kxbx vfti rpub'
MAIL_DEFAULT_SENDER = 'sahilodedra26@gmail.com'