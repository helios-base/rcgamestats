from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, IntegerField, TextAreaField, SelectMultipleField
from wtforms.validators import Optional, NumberRange, DataRequired, Length, ValidationError


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
        validators=[
            DataRequired("Please enter the number of matches"),
            NumberRange(min=1, message="Number of matches must be greater than or equal to 1")]
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
        if number_of_matches.data < 1 or 10000 < number_of_matches.data:
            raise ValidationError("Number of matches must be within [1, 10000]")
        return True


class GroupEditForm(FlaskForm):
    """
    Form for users to edit a group
    """
    additional_matches = IntegerField(
        "Additional Matches",
        validators=[NumberRange(min=0, message="Number of matches must be greater than or equal to 0")],
        default=0
    )
    description = TextAreaField(
        "Description",
        validators=[Length(min=0, max=256, message="Description must be less than 256 characters")]
    )
    submit = SubmitField("Submit")

    def validate_additional_matches(self, additional_matches):
        if additional_matches.data < 0:
            raise ValidationError("Number of matches must be greater than or equal to 0")
        return True


class RoundrobinCreateForm(FlaskForm):
    left_teams = SelectMultipleField(
        "Left Teams",
        choices=[],
        coerce=int,
        validators=[DataRequired("Please select at least one team for the left column")],
        render_kw={"style": "padding-right: 10px;"}
    )
    right_teams = SelectMultipleField(
        "Right Teams",
        choices=[],
        coerce=int,
        validators=[DataRequired("Please select at least one team for the right column")],
        render_kw={"style": "padding-right: 10px;"}
    )
    number_of_matches = IntegerField(
        "# of Matches for Each Pair",
        validators=[DataRequired("Please enter the number of matches")]
    )
    submit = SubmitField("Submit")

    def validate_number_of_matches(self, number_of_matches):
        if number_of_matches.data < 1 or 10000 < number_of_matches.data:
            raise ValidationError("Number of matches must be within [1, 10000]")
        return True
