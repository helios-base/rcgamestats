from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional, Regexp
from rcgame_flask.auth.models import User


class LoginForm(FlaskForm):
    """
    Login form input class
    """

    username = StringField(
        "Username or Email: ", 
        validators=[DataRequired("username is required")]
    )
    password = PasswordField(
        "Password: ",
        validators=[
            DataRequired("password is required"),
            Length(4, 32, "Password must be between 4 and 32 characters")
        ],
    )
    submit = SubmitField("Login")


class UserRegistrationForm(FlaskForm):
    """
    User registration form input class
    """

    username = StringField(
        "Username (optional): ",
        validators=[
            Optional("username is optional"),
            Length(2, 16, "Username must be between 2 and 16 characters"),
            Regexp(
                r"^[a-zA-Z0-9][a-zA-Z0-9+_.-]*$",
                message="Username must start with an alphanumeric and be alphanumeric and +, -, _ or .",
            ),
            ],
    )
    email = EmailField(
        "Email: ",
        validators=[DataRequired("email address is required")]
    )
    password = PasswordField(
        "Password: ",
        validators=[
            DataRequired("password is required"),
            Length(4, 32, "Password must be between 4 and 32 characters"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password: ",
        validators=[
            DataRequired("confirm password is required"),
            EqualTo("password", "Passwords must match"),
        ],
    )
    type = SelectField(
        "User Type: ",
        choices=[("user", "User"), ("admin", "Admin")],
        default="user",
    )

    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("username already exists")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("email address already exists")

    def validate_password(self, password):
        UserRegistrationForm.validate_password_strength(password)

    # check if the password contains both letters and numbers
    @staticmethod
    def validate_password_strength(password):
        if not (
            any(c.isalpha() for c in password.data)
            and any(c.isdigit() for c in password.data)
        ):
            raise ValidationError("Password must contain both letters and numbers")


class PasswordChangeForm(FlaskForm):
    """
    Password change form input class
    """

    current_password = PasswordField(
        "Current Password: ",
        validators=[DataRequired("current password is required")],
    )
    new_password = PasswordField(
        "New Password: ",
        validators=[
            DataRequired("new password is required"),
            Length(4, 32, "Password must be between 4 and 32 characters"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password: ",
        validators=[
            DataRequired("confirm password is required"),
            EqualTo("new_password", "Passwords must match"),
        ],
    )
    submit = SubmitField("Change Password")

    # check if the password contains both letters and numbers
    def validate_new_password(self, new_password):
        UserRegistrationForm.validate_password_strength(new_password)
