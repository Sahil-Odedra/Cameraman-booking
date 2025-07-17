db_user="root"
db_password=""
db_name="cameraman_booking"
db_host="localhost"

SQLALCHEMY_DATABASE_URI=f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
SQLALCHEMY_TRACK_MODIFICATIONS=False