from itsdangerous import URLSafeTimedSerializer
from flask import current_app

from flask_mail import Mail, Message
from flask import url_for

mail = Mail()

def send_confirmation_email(user_email, token):
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    subject = "ОСТАЛОСЬ утвердить ПОЧТение твое"
    html = f"""
    <p>Для завершения регистрации перейдите по ссылке:</p>
    <a href="{confirm_url}">{confirm_url}</a>
    <p>Ссылка действительна в течение часа.</p>
    <br>
    <p>И да, это не корпоратик почта, а моя личная, чтобы доверяли вы мне.</p>
    <strong>3СЛИ не ЖМЯКАЕТСЯ, то РУ4КАми Ctrl+C Ctrl+V в строку адреса от твоего интернет-обозревателя.</strong>
    """
    send_message(user_email, subject, html)

def send_password_reset_email(user_email, token):
    confirm_url = url_for('auth.reset_password', token=token, _external=True)
    subject = "Сброс пароля. Кофе помогает от Альцгеймера"
    html = f"""
        <p>Для сброса пароля шлепайте по ссылке:</p>
        <a href="{confirm_url}">{confirm_url}</a>
        <p>Ссылка действительна в течение часа.</p>
        <br>
        <p>И да, это не корпоратик почта, а моя личная, чтобы доверяли вы мне.</p>
        <strong>3СЛИ не ЖМЯКАЕТСЯ, то РУ4КАми Ctrl+C Ctrl+V в строку адреса от твоего интернет-обозревателя.</strong>
        """
    send_message(user_email, subject, html)

def send_message(user_email, subject, html):
    msg = Message(subject, recipients=[user_email], html=html, sender=current_app.config.get('MAIL_DEFAULT_SENDER'))
    mail.send(msg)

def send_massive_message(user_emails, subject, html):
    if user_emails:
        msg = Message(subject, recipients=user_emails, html=html, sender=current_app.config.get('MAIL_DEFAULT_SENDER'))
        mail.send(msg)

# TODO: 0.6.1 вынести хард-код
def send_notification_post(user_emails, post, update=False):
    html = f"""
        <!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="max-width: 600px; margin: 0 auto; background: #4e4848; font-family: sans-serif; padding: 1rem;">

    <article style="background: #4e4848; padding: 0.5rem 0; border-bottom: 1px solid lightgray;">

        <header style="display: flex; align-items: flex-end; font-size: 0.85em;">
            <div style="flex: auto;">
                <h1 style="font-family: serif; color: #de4f18; font-size: 1.5em; margin: 0 0 0.25rem 0;">
                    {post.title}
                </h1>
                <div style="color: #007dff; font-style: italic;">
                    by {post.author.username} on {post.created.strftime('%Y-%m-%d')}
                </div>
            </div>
        </header>

        <p style="white-space: pre-line; margin: 0.5rem 0; color: #fff; font-family: sans-serif;">
            {post.body}
        </p>
        
        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
            <a href="{url_for('blog.view', id=post.id, _external=True)}" 
               style="color: #ff0000; text-decoration: none;">
                Посмотреть на МММ →
            </a>
        </p>

    </article>

</body>
</html>
    """

    if update:
        theme = "УВЕДОМЛЕНИЕ - Изменение публикации на МММ: "
    else:
        theme = "УВЕДОМЛЕНИЕ - Новая публикация на МММ: "
    send_massive_message(user_emails, theme + post.title, html)


def send_notification_author(user_emails, post, author_username):
    html = f"""
        <!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="max-width: 600px; margin: 0 auto; background: #4e4848; font-family: sans-serif; padding: 1rem;">

    <article style="background: #4e4848; padding: 0.5rem 0; border-bottom: 1px solid lightgray;">

        <header style="display: flex; align-items: flex-end; font-size: 0.85em;">
            <div style="flex: auto;">
                <h1 style="font-family: serif; color: #de4f18; font-size: 1.5em; margin: 0 0 0.25rem 0;">
                    {post.title}
                </h1>
                <div style="color: #007dff; font-style: italic;">
                    by {post.author.username} on {post.created.strftime('%Y-%m-%d')}
                </div>
            </div>
        </header>

        <p style="white-space: pre-line; margin: 0.5rem 0; color: #fff; font-family: sans-serif;">
            {post.body}
        </p>

        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
            <a href="{url_for('blog.view', id=post.id, _external=True)}" 
               style="color: #ff0000; text-decoration: none;">
                Посмотреть на МММ →
            </a>
        </p>

    </article>

</body>
</html>
    """

    send_massive_message(user_emails, f"УВЕДОМЛЕНИЕ - Новая публикация от автора {author_username}: " + post.title, html)

def send_notification_comment(user_email, comment):
    html = f"""
        <!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="max-width: 600px; margin: 0 auto; background: #4e4848; font-family: sans-serif; padding: 1rem;">

    <article style="background: #4e4848; padding: 0.5rem 0; border-bottom: 1px solid lightgray;">

        <header style="display: flex; align-items: flex-end; font-size: 0.85em; margin-bottom: 0.25rem;">
            <div style="flex: auto;">
                <div style="color: #007dff; font-style: italic;">
                    {comment.author.username} commented on {comment.created.strftime('%Y-%m-%d')}
                </div>
            </div>
        </header>

        <p style="white-space: pre-line; margin: 0.5rem 0; color: #ffffff; font-family: sans-serif; font-size: 1rem; line-height: 1.4;">
            {comment.body}
        </p>

        <p style="margin-top: 0.5rem; font-size: 0.85rem;">
            <a href="{url_for('blog.view', id=comment.post_id, _external=True)}" 
               style="color: #ff0000; text-decoration: none;">
                Посмотреть обсуждение →
            </a>
        </p>

    </article>

</body>
</html>
    """

    send_massive_message(user_email, f"УВЕДОМЛЕНИЕ - Новый комментарий под постом {comment.post.title}", html)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config.get('SALT_KEY_EMAIL_VERIFICATION'))

def confirm_token(token):
    expiration = current_app.config.get('CONFIRMATION_TOKEN_EXPIRATION')

    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config.get('SALT_KEY_EMAIL_VERIFICATION'),
            max_age=expiration
        )
    except:
        return None
    return email