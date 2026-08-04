import functools
import string
from datetime import datetime

import flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from . import db
from .models import User
from .utils import generate_confirmation_token, send_confirmation_email, confirm_token

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        error = None


        if not password:
            error = 'Пароль тоже нужен.'


        error = check_username(username) or error

        error = check_email(email) or error

        if error is None:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                error = "Ошибка при регистрации."
            else:
                token = generate_confirmation_token(email)
                send_confirmation_email(email, token)
                flash('PR0верь твоего ПОЧТенного гонца! {перевод для нормисов (не будь им!?): чекни почту}')
                return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Неправильное имя.'
        elif not user.check_password(password):
            error = 'Неправильный пароль.'
        elif not user.verified and user.email:
            print(user.email)
            error = 'Сначала проверь почтовичка в спаме! И утверди деяние!'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('ОП0ЗДАЛ тВОЙ гонец... Или ты сам! Попробуй изнова!')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('Такого нет человека 0_0')
        return redirect(url_for('login'))
    if user.verified:
        flash('Усё уже готово, человек (?)')
    else:
        user.verified = True
        db.session.commit()
        flash('М0ЛОДЦА! Теперь ты можешь войти.')
    return redirect(url_for('auth.login'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

def delete_verified(exciting_user):
    if not exciting_user:
        return None
    if exciting_user.verified == False and exciting_user.email and (
            datetime.utcnow() - exciting_user.created_at).total_seconds() > flask.current_app.config.get(
        'CONFIRMATION_TOKEN_EXPIRATION', 3600):
        db.session.delete(exciting_user)
        db.session.commit()
        return None
    return exciting_user

def check_username(username: str, check_exc=True):
    if not username:
        return 'Имя нужно.'
    elif len(username) > 20:
        return 'ТЫ СЛИШКОМ ДОЛГО ЗОВЕШЬСЯ'
    elif not set(username).issubset(set(string.ascii_letters + string.digits + string.punctuation)):
        return 'пожалуйста, не выпендривайтесь и используйте в своём нике только латиницу, цифры и спецсимволы'
    exciting_user = delete_verified(User.query.filter_by(username=username).first())

    if exciting_user and check_exc:
        return f"Пользователь с именем {username} уже зарегистрирован."
    return None

def check_email(email: str, check_exc=True):
    if not email:
        return 'Почтовичка забыли!'
    elif (not email) or ('@' not in email) or ('.' not in email):
        return 'Некорректная почта'

    exciting_user = delete_verified(User.query.filter_by(email=email).first())

    if exciting_user and check_exc:
        return f"Пользователь с почтой {email} уже зарегистрирован."
    return None
