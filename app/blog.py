from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required

from . import db
from .models import Post, User

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    posts = db.session.query(Post).join(User).order_by(Post.created.desc()).all()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Как корабль назовешь, так он и поплывет! Назови.'

        if error is not None:
            flash(error)
        else:
            new_post = Post(title=title, body=body, author=g.user)
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
        error = None

        if not title:
            error = 'Название нужно.'

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
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
