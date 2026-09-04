import string

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from sqlalchemy import or_
from werkzeug.exceptions import abort

from mmm.auth import login_required

from . import db
from .models import Post, User, Vote, Comment, Subscribes
from .utils import send_notification_post, send_notification_comment, send_notification_author

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    tag = request.args.get('tag')
    search = request.args.get('search')
    sort = request.args.get('sort')

    max_pages = int(request.args.get('max_pages', current_app.config.get('DEFAULT_MAX_PAGES', 10)))
    page = int(request.args.get('page', 1))

    query = db.session.query(Post).join(User)

    if tag:
        query = query.filter(
            or_(
                Post.tags == tag,
                Post.tags.like(f'{tag} %'),
                Post.tags.like(f'% {tag} %'),
                Post.tags.like(f'% {tag}')
            )
        )
    if search:
        query = query.filter(
            or_(
                Post.title.like(f'%{search}%'),
                Post.body.like(f'%{search}%')
            )
        )
    if sort == 'new' or not sort:
        query = query.order_by(Post.created.desc())
    elif sort == 'old':
        query = query.order_by(Post.created.asc())
    elif sort == 'best':
        query = query.order_by(Post.rating.desc())
    elif sort == 'worst':
        query = query.order_by(Post.rating.asc())
    posts = query.paginate(page=page, per_page=max_pages, max_per_page=100, error_out=True)
    return render_template('blog/index.html', posts=posts, current_tag=tag, page=page)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags']
        error = None

        if not title:
            error = 'Как корабль назовешь, так он и поплывет! Назови.'
        if len(title) > 70:
            error = 'Большое название 0_0'
        if not set(tags).issubset(set(string.ascii_lowercase + string.digits + " абвгдеёжзийклмнопрстуфхцчшщъыьэюя_-")):
            error = 'Пишите теги только строчными буквами {перевод для нормисов: маленькими} разделяя их проблемами. Пример: нога демократия апокалипсис тарелка а_вы_знали'
        if len(tags) > 200:
            error = 'Слишком много меток/метки слишком большие/метки слишком большие и их слишком много'

        if error is not None:
            flash(error)
        else:
            new_post = Post(title=title, body=body, author=g.user, tags=tags)
            db.session().add(new_post)
            db.session.commit()

            send_notification_post(get_global_subscribers_emails() , new_post)
            send_notification_author(get_author_subscribers_emails(g.user.id), new_post, g.user.username)

            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = Post.query.join(User).filter(Post.id == id).first()

    if post is None:
        abort(404, f"Публикация под номером {id} не существует!")

    if check_author and post.author_id != g.user.id and g.user.id != 1: #TODO: нормальная админка
        abort(403, "Это не твоя публикация, ушлёпок!")

    return post

def get_comment(id, post_id, check_author=True):
    comment = Comment.query.filter(Comment.id == id, Comment.post_id == post_id).first()
    if not comment:
        abort(400, "Такого комментария нет")
    if comment.author_id != g.user.id and g.user.id != 1:  # TODO: убрать тестовую админку и сделать нормальную
        abort(400, "Не твой комментарий")

    return comment

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        tags = request.form['tags']
        error = None

        if not title:
            error = 'Как корабль назовешь, так он и поплывет! Назови.'
        if len(title) > 70:
            error = 'Большое название 0_0'
        if not set(tags).issubset(set(string.ascii_lowercase + string.digits + " абвгдеёжзийклмнопрстуфхцчшщъыьэюя_-")):
            error = 'Пишите теги только строчными буквами {перевод для нормисов: маленькими} разделяя их проблемами. Пример: нога демократия апокалипсис тарелка а_вы_знали'
        if len(tags) > 200:
            error = 'Слишком много меток/метки слишком большие/метки слишком большие и их слишком много'

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            post.tags = tags
            db.session.commit()

            post = get_post(id)
            send_notification_post(get_post_subscribers_emails(id), post, update=True)

            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()
    flash("Публикация удаленААА")

    return redirect(url_for('blog.index'))

@bp.route('/<int:id>')
def view(id):
    post = get_post(id, False)
    return render_template('blog/view.html', post=post)

# TODO: вынести в блюпринт комментариев (0.6.1)
@bp.route('/<int:post_id>/comments/<int:comment_id>', methods=('GET', 'POST'))
@login_required
def update_comment(post_id, comment_id):
    comment = get_comment(comment_id, post_id)
    if request.method == 'POST':
        body = request.form.get('body', type=str)
        comment_validator(body)
        comment.body = body
        db.session.commit()
        flash("Комментарий изменен")
        return redirect(url_for('blog.view', id=post_id))
    else:
        return render_template('blog/edit_comment.html', comment=comment)

@bp.route('/<int:post_id>/comments/<int:comment_id>/delete', methods=('POST', 'GET'))
@login_required
def delete_comment(post_id, comment_id):
    comment = get_comment(comment_id, post_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Комментарий удален")

    return redirect(url_for('blog.view', id=post_id))

def change_vote(user_id, post_id, value):
    post = get_post(post_id, False)
    if value not in (1, -1, 0):
        raise ValueError("Голос должен быть +1, или -1, или 0")

    exciting_vote = Vote.query.filter(Vote.user_id == user_id, Vote.post_id == post_id).first()

    if exciting_vote:
        post.rating -= exciting_vote.value
        if exciting_vote.value != value:
            post.rating += value
            exciting_vote.value = value
        else:
            exciting_vote.value = 0
    else:
        post.rating += value
        new_vote = Vote(user_id=user_id, post_id=post_id, value=value)
        db.session.add(new_vote)

    db.session.commit()

@bp.route('/<int:id>/vote', methods=('POST',))
@login_required
def vote(id):
    value = request.form.get('value', type=int)
    try:
        change_vote(g.user.id, id, value)
    except ValueError as e:
        abort(400, str(e))

    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/comments', methods=('POST',))
@login_required
def post_comment(id):
    post = get_post(id, False)
    body = request.form.get('body', type=str)
    comment_validator(body)
    new_comment = Comment(body=body, author_id=g.user.id, post_id=post.id)
    db.session.add(new_comment)
    db.session.commit()

    emails = get_post_subscribers_emails(id)
    if emails:
        send_notification_comment(emails, new_comment)

    return redirect(url_for('blog.view', id=id))

def comment_validator(body):
    if body is None:
        abort(400, "какой смысл тебе пустые комментарии слать?")
    elif len(body) > 400:
        abort(400, "ТЫ СЛИШКОМ ДОЛГО ПИШЕШЬ КОММЕНТЫ")

# TODO: вынести эти функции в модель подписок/пользователя + вынести общий функционал функций (?) (0.6.1)
def get_global_subscribers_emails():
    query = db.session.query(User.email).join(Subscribes, User.id == Subscribes.user_id).filter(
        Subscribes.type == 'global',
    ).distinct()

    emails = [row[0] for row in query.all()]
    return emails

def get_post_subscribers_emails(post_id):
    query = db.session.query(User.email).join(Subscribes, User.id == Subscribes.user_id).filter(
        Subscribes.type == 'discussion',
        Subscribes.subject_id == post_id,
    ).distinct()

    emails = [row[0] for row in query.all()]
    return emails

def get_author_subscribers_emails(author_id):
    query = db.session.query(User.email).join(Subscribes, User.id == Subscribes.user_id).filter(
        Subscribes.type == 'author',
        Subscribes.subject_id == author_id,
    ).distinct()

    emails = [row[0] for row in query.all()]
    return emails
