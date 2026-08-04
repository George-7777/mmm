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