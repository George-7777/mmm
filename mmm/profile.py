import string

from mmm.auth import login_required, delete_verified, check_username, check_email, check_password
from datetime import datetime

import flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from . import db
from .models import User
from .utils import generate_confirmation_token, send_confirmation_email

bp = Blueprint('profile', __name__, url_prefix='/profile')


@bp.route('/add_email', methods=('GET', 'POST'))
@login_required
def add_email():
    if request.method == 'POST':
        email = request.form['email']
        error = None
        if (not email) or ('@' not in email) or ('.' not in email):
            error = 'Некорректная почта'

        exciting_user = User.query.filter_by(email=email).first()

        if exciting_user:
            if exciting_user.verified == False and (datetime.utcnow() - exciting_user.created_at).total_seconds() > flask.current_app.config.get(
                    'CONFIRMATION_TOKEN_EXPIRATION', 3600):
                db.session.delete(exciting_user)
                db.session.commit()
            else:
                error = f"Пользователь с почтой {email} уже зарегистрирован."

        if error is None:
            user = User.query.filter_by(username=g.user.username).first()
            user.email = email
            db.session.commit()
            token = generate_confirmation_token(email)
            send_confirmation_email(email, token)
            session.clear()
            flash('PR0верь твоего ПОЧТенного гонца! {перевод для нормисов (не будь им!?): чекни почту}')
            return redirect(url_for('auth.login'))
        else:
            flash(error)
            return render_template('profile/add_email.html')
    else:
        return render_template('profile/add_email.html')

@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_repeat']
        error = None
        user = User.query.filter_by(username=g.user.username).first()
        if g.user.username != username:
            error = check_username(username) or error
        if g.user.email != email:
            error = check_email(email) or error
        if password != password_confirm:
            error = 'Пароль неправильно повторен!'
        if password:
            error = check_password(password) or error

        if error is None:
            user.username = username

            if password:
                user.set_password(password)
                flash('Перелогинься с новым паролем!')
            if user.email != email:
                user.email = email
                user.verified = False
                token = generate_confirmation_token(email)
                send_confirmation_email(email, token)
                flash('PR0верь твоего ПОЧТенного гонца! {перевод для нормисов (не будь им!?): чекни почту}')
            if password or user.email != email:
                session.clear()
                db.session.commit()
                return redirect(url_for('auth.login'))
            db.session.commit()
        else:
            flash(error)
    return render_template('profile/settings.html')
