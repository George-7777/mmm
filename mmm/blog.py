import string

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from sqlalchemy import or_
from werkzeug.exceptions import abort

from mmm.auth import login_required

from . import db
from .models import Post, User, Vote, Comment

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    tag = request.args.get('tag')

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

    posts = query.order_by(Post.created.desc()).all()
    return render_template('blog/index.html', posts=posts, current_tag=tag)


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
        if len(title) > 200:
            error = 'Большое название 0_0'
        if not set(tags).issubset(set(string.ascii_lowercase + string.digits + " абвгдеёжзийклмнопрстуфхцчшщъыьэюя")):
            error = 'Пишите теги только строчными буквами {перевод для нормисов: маленькими} разделяя их проблемами. Пример: нога демократия апокалипсис тарелка'
        if len(tags) > 200:
            error = 'Слишком много меток/метки слишком большие/метки слишком большие и их слишком много'

        if error is not None:
            flash(error)
        else:
            new_post = Post(title=title, body=body, author=g.user, tags=tags)
            db.session().add(new_post)
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = Post.query.join(User).filter(Post.id == id).first()

    if post is None:
        abort(404, f"Публикация под номером {id} не существует!")

    if check_author and post.author_id != g.user.id:
        abort(403, "Это не твоя публикация, ушлёпок!")

    return post


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
        if len(title) > 200:
            error = 'Большое название 0_0'
        if not set(tags).issubset(set(string.ascii_lowercase + string.digits + " абвгдеёжзийклмнопрстуфхцчшщъыьэюя")):
            error = 'Пишите теги только строчными буквами {перевод для нормисов: маленькими} разделяя их проблемами. Пример: нога демократия апокалипсис тарелка'
        if len(tags) > 200:
            error = 'Слишком много меток/метки слишком большие/метки слишком большие и их слишком много'

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            post.tags = tags
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()

    return redirect(url_for('blog.index'))

@bp.route('/<int:id>')
def view(id):
    post = get_post(id, False)
    return render_template('blog/view.html', post=post)

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
    if body == '':
        abort(400, "какой смысл тебе пустые комментарии слать?")
    new_comment = Comment(body=body, author_id=g.user.id, post_id=post.id)
    db.session.add(new_comment)
    db.session.commit()

    return redirect(url_for('blog.view', id=id))
