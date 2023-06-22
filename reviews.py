from flask import Blueprint, render_template, request, redirect, flash, url_for
from models import db, Book, Cover, Genre, Review, User
from flask_login import current_user, login_required
from bleach import clean
# from flask_paginate import Pagination, get_page_args


bp = Blueprint('reviews', __name__)


@bp.route('/add_review/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    book = Book.query.get(book_id)
    existing_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()

    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации")
        return redirect(url_for('auth.login'))

    if existing_review:
        # Если пользователь уже написал рецензию на данную книгу,
        # отображаем его рецензию
        return render_template('review.html', book=book, review=existing_review)

    if request.method == 'POST':
        rating = int(request.form['rating'])
        text = clean(request.form['comment'], tags=[], attributes={}, protocols=[], strip=True)

        review = Review(book_id=book_id, user_id=current_user.id, rating=rating, text=text, status_id=1)
        db.session.add(review)
        db.session.commit()

        flash('Рецензия успешно добавлена', 'success')
        return redirect(f'/book/{book_id}')

    return render_template('add_review.html', book=book)

@bp.route('/my_reviews')
@login_required
def my_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    for review in reviews:
        book = Book.query.get(review.book_id)
        review.book_title = book.title
        review.book_author = book.author
        review.book_cover = book.cover.filename
    return render_template('my_reviews.html', reviews=reviews)


@bp.route('/moderate')
@login_required
def moderate_reviews():
    # Получаем номер текущей страницы и количество элементов на странице из запроса
    # page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')

    # Запрашиваем только рецензии со статусом 1, сортируем их по дате добавления в обратном порядке
    reviews = Review.query.filter_by(status_id=1).order_by(Review.date_added.desc()).limit(per_page).offset(offset).all()

    for review in reviews:
        user = User.query.get(review.user_id)
        book = Book.query.get(review.book_id)
        review.first_name = user.first_name
        review.book_title = book.title
        review.added_date = review.date_added.strftime('%d.%m.%Y %H:%M')

    # Получаем общее количество рецензий со статусом 1
    total_reviews = Review.query.filter_by(status_id=1).count()

    # Создаем объект Pagination
    # pagination = Pagination(page=page, per_page=per_page, total=total_reviews, css_framework='bootstrap4')

    # return render_template('moderate.html', reviews=reviews, pagination=pagination)
    return render_template('moderate.html', reviews=reviews)


@bp.route('/review/<int:review_id>', methods=['GET', 'POST'])
@login_required
def review(review_id):
    review = Review.query.get(review_id)
    user = User.query.get(review.user_id)
    book = Book.query.get(review.book_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            review.status_id = 2  # Устанавливаем статус "Одобрено"
            db.session.commit()
            flash('Рецензия одобрена', 'success')
        elif action == 'reject':
            review.status_id = 3  # Устанавливаем статус "Отклонено"
            db.session.commit()
            flash('Рецензия отклонена', 'success')
        return redirect(url_for('reviews.moderate_reviews'))

    return render_template('review.html', review=review, user=user, book=book)