SECRET_KEY = "1"

HOSTNAME = "host.docker.internal"
PORT= "3306"
USERNAME="root"
PASSWORD="11111111"
DATABASE= "new_schema_1"

DB_URI = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
SQLALCHEMY_DATABASE_URI = DB_URI


