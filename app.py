from flask import Flask, render_template, request, redirect, flash
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
from models import db, Book, Cover, Review, User, Role, Genre
from auth import bp as auth_bp
from library import bp as library_bp
from flask_login import LoginManager, current_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = SECRET_KEY

db.init_app(app)


@app.cli.command()
def migrate():
    with app.app_context():
        db.create_all()


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(library_bp)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))


if __name__ == '__main__':
    app.run()