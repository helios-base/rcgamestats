from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError
from rcgame_flask.auth.models import User


class LoginForm(FlaskForm):
    """
    Login form input class
    """
    username = StringField(
        "Username: ", validators=[DataRequired("username is required")]
    )
    password = PasswordField(
        "Password: ",
        validators=[Length(4, 10, "Password must be between 4 and 10 characters")],
    )
    submit = SubmitField("Login")

class SignUpForm(LoginForm):
    """
    Singup form input class
    """
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("username already exists")

    # check if the password contains both letters and numbers
    def validate_password(self, password):
        if not (
            any(c.isalpha() for c in password.data)
            and any(c.isdigit() for c in password.data)
        ):
            raise ValidationError("Password must contain both letters and numbers")
