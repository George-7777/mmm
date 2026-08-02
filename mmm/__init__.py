import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate
from flask_mail import Mail

mail = Mail()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=app.config.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'mmm.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    db.init_app(app)
    mail.init_app(app)

    migrate = Migrate(app, db)

    from . import auth, blog, models, profile

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(profile.bp)
    app.add_url_rule('/', endpoint='index')

    return app