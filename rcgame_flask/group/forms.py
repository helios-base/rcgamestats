from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class GroupCreateForm(FlaskForm):
    """
    Form for users to create a new group
    """
    team_left = SelectField(
        "Left Team",
        choices=[],
        coerce=int
    )
    team_right = SelectField(
        "Right Team",
        choices=[],
        coerce=int
    )
    number_of_matches = IntegerField(
        "# of Matches",
        validators=[DataRequired("Please enter the number of matches")]
    )
    description = TextAreaField(
        "Description",
        validators=[Length(min=0, max=256)]
    )
    submit = SubmitField("Submit")

    def validate(self, extra_validators=None):
        if not super(GroupCreateForm, self).validate(extra_validators=extra_validators):
            return False
        if self.team_left.data == self.team_right.data:
            self.team_right.errors.append("Left and right teams must be different")
            return False
        return True

    def validate_number_of_matches(self, number_of_matches):
        if number_of_matches.data < 1:
            raise ValidationError("Number of matches must be at least 1")
