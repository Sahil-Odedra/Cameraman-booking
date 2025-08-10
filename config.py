db_user="root"
db_password=""
db_name="cameraman_booking"
db_host="host.docker.internal"

SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
SQLALCHEMY_TRACK_MODIFICATIONS=False

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your Email'
MAIL_PASSWORD = 'Your Key'
MAIL_DEFAULT_SENDER = 'Your Email'