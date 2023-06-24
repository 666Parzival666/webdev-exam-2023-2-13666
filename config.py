import os

SECRET_KEY = 'your_secret_key'

SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://666Parzival666:Robsalvatore13@666Parzival666.mysql.pythonanywhere-services.com/666Parzival666$grearLibrary'
# SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://sql10627580:5cIXjyr3VL@sql10.freesqldatabase.com/sql10627580'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'covers')