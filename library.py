from flask import Blueprint, render_template, request, redirect, flash, url_for
from models import db, Book, Cover, Genre, Review, User
from werkzeug.utils import secure_filename
from flask_login import current_user
import os
import hashlib
from bleach import clean
from config import UPLOAD_FOLDER
from sqlalchemy.exc import SQLAlchemyError
import markdown2
from markdown2 import markdown

bp = Blueprint('library', __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/')
def index():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10

        books_pagination = Book.query.order_by(Book.year.desc(), Book.title) \
            .paginate(page=page, per_page=per_page, error_out=False)
        books = books_pagination.items

        genres = Genre.query.all()

        for book in books:
            reviews = Review.query.filter_by(book_id=book.id, status_id=2).all()
            ratings = [review.rating for review in reviews]
            average_rating = sum(ratings) / len(ratings) if ratings else 0
            average_rating = round(average_rating, 2)
            reviews_count = len(reviews)
            book.average_rating = average_rating
            book.reviews_count = reviews_count

        # user_review = None
        # if current_user.is_authenticated:
        #     user_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()

        return render_template('library/index.html', books=books, genres=genres, pagination=books_pagination)
    except SQLAlchemyError:
        flash('Произошла ошибка базы данных', 'error')
        return redirect(url_for('library.index'))


@bp.route('/book/<int:book_id>')
def view_book(book_id):
    try:
        book = Book.query.get(book_id)
        reviews = Review.query.filter_by(book_id=book.id, status_id=2).all()

        if current_user.is_authenticated:
            user_review = Review.query.filter_by(book_id=book.id, user_id=current_user.id).first()
            if user_review:
                user_review.text = markdown2.markdown(user_review.text, extras=['fenced-code-blocks', 'cuddled-lists', 'metadata', 'tables', 'spoiler'])
            else:
                user_review = None
        else:
            user_review = None

        ratings = [review.rating for review in reviews]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        average_rating = round(average_rating, 2)
        reviews_count = len(reviews)

        book.average_rating = average_rating

        for review in reviews:
            user = User.query.get(review.user_id)
            review.user_name = f"{user.first_name} {user.last_name}"
            review.text = markdown2.markdown(review.text, extras=['fenced-code-blocks', 'cuddled-lists', 'metadata', 'tables', 'spoiler'])

        book.reviews_count = reviews_count
        if book.description:
            try:
                # Пытаемся преобразовать содержимое поля book.description из Markdown в HTML
                book.description = markdown(book.description,
                                            extras=['fenced-code-blocks', 'cuddled-lists', 'metadata', 'tables',
                                                    'spoiler'])
            except Exception:
                # Если возникает ошибка (например, если содержимое не является разметкой Markdown),
                # то оставляем поле без изменений
                pass

        return render_template('library/book.html', book=book, reviews=reviews, average_rating=average_rating, reviews_count=reviews_count, user_review=user_review)
    except SQLAlchemyError:
        flash('Произошла ошибка базы данных', 'error')
        return redirect(url_for('library.index'))


@bp.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации", 'error')
        return redirect(url_for('auth.login'))

    if current_user.role_id != 1:  # Assuming admin role ID is 1
        flash("У вас недостаточно прав для выполнения данного действия", 'error')
        return redirect(url_for('library.index'))

    if request.method == 'POST':
        try:
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

            cover_md5 = hashlib.md5(cover_file.read()).hexdigest()

            # Проверяем, существует ли уже обложка с таким хэшем
            existing_cover = Cover.query.filter_by(md5_hash=cover_md5).first()
            if existing_cover:
                cover_id = existing_cover.id
                filename = existing_cover.filename
            else:
                # Сохраняем файл обложки
                filename = secure_filename(cover_file.filename)
                cover_path = os.path.join(UPLOAD_FOLDER, filename)
                cover_file.seek(0)
                cover_file.save(cover_path)

                # Получаем новый идентификатор для обложки
                cover_id = Cover.query.order_by(Cover.id.desc()).first().id + 1

                # Переименовываем файл
                new_filename = f"{cover_id}{os.path.splitext(filename)[-1]}"
                new_cover_path = os.path.join(UPLOAD_FOLDER, new_filename)
                os.rename(cover_path, new_cover_path)
                filename = new_filename

                # Создаем запись об обложке в базе данных
                new_cover = Cover(id=cover_id, filename=filename, mime_type=cover_file.mimetype, md5_hash=cover_md5)
                db.session.add(new_cover)
                db.session.commit()

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
            return redirect(url_for('library.view_book', book_id=new_book.id))

        except Exception as e:
            db.session.rollback()  # Откатываем изменения в базе данных
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'error')
            return render_template('add_book.html', genres=Genre.query.all(), add_mode=True)

    # Если метод GET, отображаем форму добавления книги
    genres = Genre.query.all()
    return render_template('library/add_book.html', genres=genres, add_mode=True)


@bp.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get(book_id)
    genres = Genre.query.all()

    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации", 'error')
        return redirect(url_for('auth.login'))

    if current_user.role_id > 2:
        flash("У вас недостаточно прав для выполнения данного действия", 'error')
        return redirect(url_for('library.index'))

    if request.method == 'POST':
        try:
            # Получаем все данные из формы редактирования книги
            title = request.form['title']
            description = clean(request.form['description'], tags=[], attributes={}, protocols=[], strip=True)
            year = int(request.form['year'])
            publisher = request.form['publisher']
            author = request.form['author']
            pages = int(request.form['pages'])
            genres = request.form.getlist('genres')

            # Обновляем данные книги в базе данных
            book.title = title
            book.description = description
            book.year = year
            book.publisher = publisher
            book.author = author
            book.pages = pages
            book.genres.clear()  # Очищаем текущие жанры книги

            for genre_id in genres:
                genre = Genre.query.get(genre_id)
                if genre:
                    book.genres.append(genre)  # Добавляем новые жанры книги

            db.session.commit()

            flash('Данные книги успешно обновлены', 'success')
            return redirect(url_for('library.view_book', book_id=book.id))

        except SQLAlchemyError:
            db.session.rollback()  # Откатываем изменения в базе данных
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'error')
            return render_template('edit_book.html', book=book, genres=genres)

    return render_template('library/edit_book.html', book=book, genres=genres)


@bp.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get(book_id)

    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации", 'error')
        return redirect(url_for('auth.login'))

    if current_user.role_id != 1:
        flash("У вас недостаточно прав для выполнения данного действия", 'error')
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