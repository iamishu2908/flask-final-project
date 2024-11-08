import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")


    #Database for SQLite
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///customer_feedback.db'

    #Database for Postgres
    # SQLALCHEMY_DATABASE_URI = 'postgresql://<username>:<password>@localhost:5432/<database name>'
    
    #Database for MySQL

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:Welcome$24@localhost/customer_records'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
