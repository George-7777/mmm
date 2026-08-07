from datetime import datetime

from sqlalchemy.engine import default
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    verified = db.Column(db.Boolean, default=False, server_default='0')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    description = db.Column(db.Text, nullable=True)
    show_email = db.Column(db.Boolean, default=False, server_default='0', nullable=False)

    posts = db.relationship('Post', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    subscribes = db.relationship('Subscribes', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_subscribed_to_global(self):
        return Subscribes.query.filter_by(
            user_id=self.id,
            type='global',
        ).first() is not None

    def is_subscribed_to_author(self, author_id):
        return Subscribes.query.filter_by(
            user_id=self.id,
            type='author',
            subject_id=author_id
        ).first() is not None

    def is_subscribed_to_post(self, post_id):
        return Subscribes.query.filter_by(
            user_id=self.id,
            type='discussion',
            subject_id=post_id
        ).first() is not None

    def subscribe_to_global(self):
        if not self.is_subscribed_to_global():
            sub = Subscribes(user_id=self.id, type='global', subject_id=-1)
            db.session.add(sub)
            db.session.commit()

    def unsubscribe_from_global(self):
        sub = Subscribes.query.filter_by(
            user_id=self.id,
            type='global',
        ).first()
        if sub:
            db.session.delete(sub)
            db.session.commit()

    def subscribe_to_author(self, author_id):
        if not self.is_subscribed_to_author(author_id):
            sub = Subscribes(user_id=self.id, type='author', subject_id=author_id)
            db.session.add(sub)
            db.session.commit()

    def unsubscribe_from_author(self, author_id):
        sub = Subscribes.query.filter_by(
            user_id=self.id,
            type='author',
            subject_id=author_id
        ).first()
        if sub:
            db.session.delete(sub)
            db.session.commit()

    def subscribe_to_post(self, post_id):
        if not self.is_subscribed_to_post(post_id):
            sub = Subscribes(user_id=self.id, type='discussion', subject_id=post_id)
            db.session.add(sub)
            db.session.commit()

    def unsubscribe_from_post(self, post_id):
        sub = Subscribes.query.filter_by(
            user_id=self.id,
            type='discussion',
            subject_id=post_id
        ).first()
        if sub:
            db.session.delete(sub)
            db.session.commit()

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, default=0, nullable=False, server_default='0')
    votes = db.relationship('Vote', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.Column(db.String(200), nullable=True, default='', server_default='')

class Vote(db.Model):
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)   # +1 или -1

    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_vote'),
        db.Index('ix_vote_post_id', 'post_id'),
    )

class Subscribes(db.Model):
    __tablename__ = 'subscribes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False) # global, discussion, author
    subject_id = db.Column(db.Integer, nullable=False, default=-1)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
