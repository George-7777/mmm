import string
from email import message

from flask_sqlalchemy.model import Model

from mmm.auth import login_required, delete_verified, check_username, check_email, check_password
from datetime import datetime

import flask
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app, abort
)

from . import db
from .models import User, Post, Comment
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
        sub_global = request.form.get('subscribe')

        description = request.form.get('description')
        show_email = request.form.get('show_email')

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

            if sub_global:
                user.subscribe_to_global()
            else:
                user.unsubscribe_from_global()

            if show_email:
                user.show_email = True
            else:
                user.show_email = False

            if description:
                user.description = description

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

@bp.route('/subscribe/post/<int:post_id>')
@login_required
def change_sub_post(post_id):
    user = User.query.filter_by(username=g.user.username).first()
    if user.is_subscribed_to_post(post_id):
        user.unsubscribe_from_post(post_id)
        message = 'Вы отписались от обсуждения поста'
    else:
        user.subscribe_to_post(post_id)
        message = 'Вы подписались на обсуждение поста'

    flash(message)

    return redirect(url_for('blog.view', id=post_id))

@bp.route('/subscribe/user/<int:user_id>')
@login_required
def change_subscribe_user(user_id):
    user = User.query.filter_by(username=g.user.username).first()
    if user.is_subscribed_to_author(user_id):
        user.unsubscribe_from_author(user_id)
        msg = 'Вы отписались от автора'
    else:
        user.subscribe_to_author(user_id)
        msg = 'Вы подписались на автора'

    flash(msg)

    return redirect(url_for('profile.view', user_id=user_id))

@bp.route('/<int:user_id>')
def view(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        abort(404, "фатал ерор четрыста чтры еее. Ушлепенец dont exist")
    type_content = request.args.get('type_content')

    max_pages = int(request.args.get('max_pages', current_app.config.get('DEFAULT_MAX_PAGES', 10)))
    page = int(request.args.get('page', 1))

    if not type_content or type_content == 'post':
        type_content = "posts"
        contents = Post.query.filter(Post.author_id == user_id).paginate(page=page, per_page=max_pages, max_per_page=100, error_out=True)
    else:
        type_content = "comments"
        contents = Comment.query.filter(Comment.author_id == user_id).paginate(page=page, per_page=max_pages, max_per_page=100, error_out=True)

    return render_template('profile/view.html', user=user, type_content=type_content, content=contents)
