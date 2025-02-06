from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError
from rcgame_flask.auth.models import User


class LoginForm(FlaskForm):
    """
    ログイン用入力クラス
    """

    username = StringField('ユーザー名：', 
                           validators=[DataRequired('ユーザー名は必須入力です')])
    # パスワード：パスワード入力
    password = PasswordField('パスワード: ',
                             validators=[Length(4, 10,
                                    'パスワードの長さは4文字以上10文字以内です')])
    # ボタン
    submit = SubmitField('ログイン')

    # カスタムバリデータ
    # 英数字と記号が含まれているかチェックする
    def validate_password(self, password):
        if not (any(c.isalpha() for c in password.data) and \
            any(c.isdigit() for c in password.data)):
            raise ValidationError('パスワードには【英数字を含める必要があります')


class SignUpForm(LoginForm):
    """
    サインアップ用入力クラス
    """

    # ボタン                               
    submit = SubmitField('サインアップ')

    # カスタムバリデータ
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('そのユーザー名は既に使用されています')
























