from flask import Blueprint, render_template, request, redirect, flash, url_for
from models import db, Book, Cover, Genre, Review
from werkzeug.utils import secure_filename
from flask_login import current_user
import os
import hashlib
from bleach import clean
from config import UPLOAD_FOLDER

bp = Blueprint('library', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    books_pagination = Book.query.order_by(Book.year.desc()).paginate(page=page, per_page=per_page, error_out=False)
    books = books_pagination.items

    genres = Genre.query.all()

    for book in books:
        reviews = Review.query.filter_by(book_id=book.id).all()
        ratings = [review.rating for review in reviews]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        reviews_count = len(reviews)
        book.average_rating = average_rating
        book.reviews_count = reviews_count

    return render_template('index.html', books=books, genres=genres, pagination=books_pagination)


@bp.route('/book/<int:book_id>')
def view_book(book_id):
    book = Book.query.get(book_id)
    reviews = Review.query.filter_by(book_id=book.id).all()
    ratings = [review.rating for review in reviews]
    average_rating = sum(ratings) / len(ratings) if ratings else 0
    reviews_count = len(reviews)
    book.average_rating = average_rating
    book.reviews_count = reviews_count

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()

    # Если пользователь авторизован и оставил рецензию, перемещаем его рецензию в начало списка
    if user_review:
        reviews.remove(user_review)
        reviews.insert(0, user_review)

    return render_template('book.html', book=book, reviews=reviews, average_rating=average_rating, reviews_count=reviews_count, user_review=user_review)


@bp.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации")
        return redirect(url_for('auth.login'))

    if current_user.role_id != 1:  # Assuming admin role ID is 1
        flash("У вас недостаточно прав для выполнения данного действия")
        return redirect(url_for('library.index'))
    if request.method == 'POST':
        title = request.form['title']
        description = clean(request.form['description'], tags=[], attributes={}, protocols=[], strip=True)
        year = int(request.form['year'])
        publisher = request.form['publisher']
        author = request.form['author']
        pages = int(request.form['pages'])
        genres = request.form.getlist('genres')

        if 'cover' not in request.files:
            flash('Необходимо загрузить обложку книги', 'error')
            return redirect(request.referrer)

        cover_file = request.files['cover']
        if cover_file.filename == '':
            flash('Необходимо выбрать файл обложки', 'error')
            return redirect(request.referrer)

        if not allowed_file(cover_file.filename):
            flash('Недопустимый тип файла. Разрешены только изображения форматов JPG, JPEG и PNG.', 'error')
            return redirect(request.referrer)

        filename = secure_filename(cover_file.filename)
        cover_path = os.path.join(UPLOAD_FOLDER, filename)
        cover_md5 = hashlib.md5(cover_file.read()).hexdigest()

        # Проверяем, существует ли уже обложка с таким хэшем
        existing_cover = Cover.query.filter_by(md5_hash=cover_md5).first()
        if existing_cover:
            cover_id = existing_cover.id
        else:
            # Сохраняем файл обложки
            cover_file.seek(0)
            cover_file.save(cover_path)

            # Создаем запись об обложке в базе данных
            new_cover = Cover(filename=filename, mime_type=cover_file.mimetype, md5_hash=cover_md5)
            db.session.add(new_cover)
            db.session.commit()
            cover_id = new_cover.id

        # Создаем запись о книге в базе данных
        new_book = Book(
            title=title,
            description=description,
            year=year,
            publisher=publisher,
            author=author,
            pages=pages,
            cover_id=cover_id
        )

        for genre_id in genres:
            genre = Genre.query.get(genre_id)
            if genre:
                new_book.genres.append(genre)

        db.session.add(new_book)
        db.session.commit()

        flash('Книга успешно добавлена', 'success')
        return redirect('/add_book')  # Редирект на страницу добавления книги после успешного добавления

    # Если метод GET, отображаем форму добавления книги
    genres = Genre.query.all()
    return render_template('add_book.html', genres=genres, add_mode=True)


@bp.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get(book_id)
    genres = Genre.query.all()

    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации")
        return redirect(url_for('auth.login'))

    if current_user.role_id > 2:
        flash("У вас недостаточно прав для выполнения данного действия")
        return redirect(url_for('library.index'))

    if request.method == 'POST':
        # Получите все данные из формы редактирования книги
        title = request.form['title']
        description = clean(request.form['description'], tags=[], attributes={}, protocols=[], strip=True)
        year = int(request.form['year'])
        publisher = request.form['publisher']
        author = request.form['author']
        pages = int(request.form['pages'])
        genres = request.form.getlist('genres')

        # Обновите данные книги в базе данных
        book.title = title
        book.description = description
        book.year = year
        book.publisher = publisher
        book.author = author
        book.pages = pages
        book.genres.clear()  # Очистите текущие жанры книги

        for genre_id in genres:
            genre = Genre.query.get(genre_id)
            if genre:
                book.genres.append(genre)  # Добавьте новые жанры книги

        db.session.commit()

        flash('Данные книги успешно обновлены', 'success')
        return redirect(url_for('library.view_book', book_id=book.id))

    return render_template('edit_book.html', book=book, genres=genres)


@bp.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get(book_id)

    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации")
        return redirect(url_for('auth.login'))

    if current_user.role_id != 1:
        flash("У вас недостаточно прав для выполнения данного действия")
        return redirect(url_for('library.index'))

    if book:
        try:
            cover_id = book.cover_id  # Получаем ID обложки книги
            db.session.delete(book)  # Удаляем запись о книге из базы данных
            db.session.commit()

            if cover_id:
                # Проверяем, есть ли другие книги с этой обложкой
                other_books_with_cover = Book.query.filter_by(cover_id=cover_id).count()
                if other_books_with_cover == 0:
                    # Если нет других книг с этой обложкой, удаляем файл обложки
                    cover = Cover.query.get(cover_id)
                    if cover:
                        cover_path = os.path.join(UPLOAD_FOLDER, cover.filename)
                        os.remove(cover_path)
                        db.session.delete(cover)
                        db.session.commit()

            flash('Книга успешно удалена.', 'success')
        except Exception as e:
            flash('Произошла ошибка при удалении книги.', 'error')
            bp.logger.error(f'Ошибка удаления книги с ID {book_id}: {str(e)}')
    else:
        flash('Книга не найдена.', 'error')

    return redirect(url_for('library.index'))