import os
from dotenv import load_dotenv
load_dotenv()

class Config(object):
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or "supersekrit"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    EMAIL_API=os.environ.get("EMAIL_API")
    EMAIL_DOMAIN=os.environ.get("EMAIL_DOMAIN")