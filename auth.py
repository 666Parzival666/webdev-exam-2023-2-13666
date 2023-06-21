from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import check_password_hash

from models import User

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(login=login).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash('Невозможно аутентифицироваться с указанными логином и паролем')
            return redirect(url_for('auth.login'))

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('home'))

    return render_template('auth/auth.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))