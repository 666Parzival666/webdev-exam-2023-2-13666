from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_mysqldb import MySQL
import hashlib
import os
import markdown
import bleach

library_bp = Blueprint('library', __name__)

# ...

@library_bp.route('/books/<int:book_id>', methods=['GET'])
def view_book(book_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        '''
        SELECT books.id, books.title, books.author, books.description, covers.hash
        FROM books
        JOIN covers ON books.cover_id = covers.id
        WHERE books.id = %s
        ''',
        (book_id,)
    )
    book_data = cursor.fetchone()
    cursor.close()

    if not book_data:
        flash('Книга не найдена', 'error')
        return redirect(url_for('library.book_list'))

    book = {
        'id': book_data[0],
        'title': book_data[1],
        'author': book_data[2],
        'description': book_data[3],
        'cover_hash': book_data[4],
    }

    # Преобразование описания книги из Markdown в HTML
    book['description'] = markdown.markdown(book['description'], extensions=['markdown.extensions.nl2br'])

    # Получение рецензий на книгу
    cursor = mysql.connection.cursor()
    cursor.execute(
        '''
        SELECT reviews.rating, reviews.review_text, users.username
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE reviews.book_id = %s
        ''',
        (book_id,)
    )
    reviews = cursor.fetchall()
    cursor.close()

    return render_template('view_book.html', book=book, reviews=reviews)

@library_bp.route('/books/<int:book_id>/reviews/add', methods=['GET', 'POST'])
def add_review(book_id):
    if request.method == 'POST':
        rating = int(request.form['rating'])
        review_text = request.form['review_text']

        # Проверка наличия рецензии от текущего пользователя для данной книги
        cursor = mysql.connection.cursor()
        cursor.execute(
            '''
            SELECT id
            FROM reviews
            WHERE book_id = %s AND user_id = %s
            ''',
            (book_id, current_user.id)
        )
        existing_review = cursor.fetchone()

        if existing_review:
            flash('Вы уже оставили рецензию на данную книгу', 'error')
            cursor.close()
            return redirect(url_for('library.view_book', book_id=book_id))

        # Сохранение рецензии
        cursor.execute(
            '''
            INSERT INTO reviews (rating, review_text, book_id, user_id)
            VALUES (%s, %s, %s, %s)
            ''',
            (rating, review_text, book_id, current_user.id)
        )
        mysql.connection.commit()
        cursor.close()

        flash('Рецензия успешно добавлена', 'success')
        return redirect(url_for('library.view_book', book_id=book_id))
    else:
        return render_template('add_review.html', book_id=book_id)