from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError
from rcgame_flask.models import user

# ログイン用入力クラス
class LoginForm(FlaskForm):
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
            any(c.isdigit() for c in password.data) and \
            any(c in '!@#$%^&*()' for c in password.data)):
            raise ValidationError('パスワードには【英数字と記号：!@#$%^&*()】を含める必要があります')

# サインアップ用入力クラス
class SignUpForm(LoginForm):
    # ボタン                               
    submit = SubmitField('サインアップ')

    # カスタムバリデータ
    def validate_username(self, username):
        User = user.query.filter_by(username=username.data).first()
        if User:
            raise ValidationError('そのユーザー名は既に使用されています')
























