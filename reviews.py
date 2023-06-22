from flask import Blueprint, render_template, request, redirect, flash
from models import db, Book, Cover, Genre, Review
from flask_login import current_user, login_required
from bleach import clean


bp = Blueprint('reviews', __name__)


@bp.route('/add_review/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    book = Book.query.get(book_id)
    existing_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()

    if existing_review:
        # Если пользователь уже написал рецензию на данную книгу,
        # отображаем его рецензию
        return render_template('review.html', book=book, review=existing_review)

    if request.method == 'POST':
        rating = int(request.form['rating'])
        text = clean(request.form['comment'], tags=[], attributes={}, protocols=[], strip=True)

        review = Review(book_id=book_id, user_id=current_user.id, rating=rating, text=text)
        db.session.add(review)
        db.session.commit()

        flash('Рецензия успешно добавлена', 'success')
        return redirect(f'/book/{book_id}')

    return render_template('add_review.html', book=book)