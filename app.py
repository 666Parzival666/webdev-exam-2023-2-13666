from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from auth import auth_bp, init_login_manager
from library import library_bp

app.register_blueprint(auth_bp)
app.register_blueprint(library_bp)

init_login_manager(app)

from models import Book, Cover, Review, User, Role

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()