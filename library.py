from flask import Blueprint, render_template, request, redirect, flash
from models import db, Book, Cover, Genre
from werkzeug.utils import secure_filename
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
    books = Book.query.all()
    genres = Genre.query.all()
    return render_template('index.html', books=books, genres=genres)


@bp.route('/add_book', methods=['GET', 'POST'])
def add_book():
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
    return render_template('add_book.html', genres=genres)
