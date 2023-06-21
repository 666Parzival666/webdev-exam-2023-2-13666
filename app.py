from flask import Flask, render_template, request, redirect, flash
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY
from models import db, Book, Cover, Review, User, Role, Genre
from auth import bp as auth_bp
from user_accesses import UsersPolicy
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

# class User(db.Model):
#     # ...
#
#     def can(self, action, record=None):
#         policy = UsersPolicy(record)
#         if action == 'create':
#             return policy.create()
#         elif action == 'delete':
#             return policy.delete()
#         elif action == 'show':
#             return policy.show()
#         elif action == 'update':
#             return policy.update()
#         elif action == 'show_collections':
#             return policy.show_collections()
#         else:
#             return False

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        name = request.form['name']  # Получаем значение поля "name" из формы
        genre = Genre(name=name)  # Создаем новый объект жанра
        db.session.add(genre)  # Добавляем объект жанра в сессию базы данных
        db.session.commit()  # Сохраняем изменения в базе данных
        flash('Жанр успешно добавлен.')  # Добавляем flash-сообщение об успешном добавлении жанра
        return redirect('/')  # Перенаправляем пользователя на главную страницу

    genres = Genre.query.all()  # Получаем список всех жанров из базы данных
    return render_template('index.html', genres=genres)

if __name__ == '__main__':
    app.run()