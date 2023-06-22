from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Таблица книг
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    pages = db.Column(db.Integer, nullable=False)
    cover_id = db.Column(db.Integer, db.ForeignKey('cover.id', ondelete='CASCADE'), nullable=False)
    cover = db.relationship('Cover', backref=db.backref('book', uselist=False, cascade='all, delete'))

    genres = db.relationship('Genre', secondary='book_genre', backref=db.backref('books', lazy=True, cascade='all, delete'))


# Таблица жанров
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)


# Соединительная таблица для связи книг и жанров
book_genre = db.Table('book_genre',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id', ondelete='CASCADE'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id', ondelete='CASCADE'), primary_key=True)
)


# Таблица обложек
class Cover(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(255), nullable=False)
    md5_hash = db.Column(db.String(255), nullable=False)


# Таблица статусов рецензий
class ReviewStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)


# Таблица рецензий
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())

    status_id = db.Column(db.Integer, db.ForeignKey('review_status.id'))
    status = db.relationship('ReviewStatus', backref=db.backref('reviews', lazy=True))

# Таблица пользователей
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=False)
    middle_name = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

# Таблица ролей пользователей
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)