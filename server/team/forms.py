# from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
    FileField,
    BooleanField,
    SelectField,
)
from wtforms.validators import DataRequired, Optional, Regexp, Length, ValidationError
from flask_wtf.file import FileRequired, FileAllowed


class TeamUploadForm(FlaskForm):
    """
    Team upload form input class
    """

    # def __init__(self, *args, **kwargs):
    #     super(TeamUploadForm, self).__init__(*args, **kwargs)
    #     self.version.data = datetime.now().strftime("%Y%m%d-%H%M%S")

    existing_team_name = SelectField(
        "Existing Team Name: ",
        choices=[],
        validators=[Optional()],
    )

    new_team_name = StringField(
        "New Team Name: ",
        validators=[
            Optional(),
            Length(4, 32, "team name must be between 4 and 32 characters"),
            Regexp(
                r"^[a-zA-Z0-9][a-zA-Z0-9+_]*$", message="team name must start with an alphanumeric and be alphanumeric and + or _"
            ),
        ],
    )

    version = StringField(
        "Version: (Empty for auto-generated with timestamp)",
        validators=[
            # DataRequired("team version is required"),
            Optional(),
            Length(0, 16, "team version must be less than 16 characters"),
            Regexp(
                r"^[a-zA-Z0-9][a-zA-Z0-9+-_]*$", message="team version must start with an alphanumeric and be alphanumeric and +, - or _"
            ),
        ],
    )

    synch_mode = BooleanField("Support synch_mode: ", default=True, validators=[])

    archive_file = FileField(
        "Archive File(*): ",
        validators=[
            FileRequired("team archive is required"),
            FileAllowed(["tar.gz", "tgz", "tar.xz", "txz", "zip"], "Invalid file extension. Please upload an archived file."),
        ]
    )

    description = TextAreaField(
        "Description: ",
        validators=[Length(0, 512, "description must be less than 512 characters")],
    )

    submit = SubmitField("Submit")

    def valiate(self):
        if not super(TeamUploadForm, self).validate():
            return False
        if (
            not self.existing_team_name.data or self.existing_team_name.data == ""
        ) and not self.new_team_name.data:
            self.new_team_name.errors.append("Team name is required")
            return False
        return True

    def validate_archive_file(self, archive_file):
        """
        Validate the team archive file extension
        """
        # print("validate_archive_file", archive_file.data)
        filename = archive_file.data.filename.lower()
        if (
            not filename.endswith(".tar.gz")
            and not filename.endswith(".tgz")
            and not filename.endswith(".tar.xz")
            and not filename.endswith(".txz")
            and not filename.endswith(".zip")
        ):
            raise ValidationError(
                "Invalid file extension. Please upload an archived file."
            )


class TeamEditForm(FlaskForm):
    """
    Team edit form input class
    """
    description = TextAreaField(
        "Edit Team Description: ",
        validators=[Length(0, 512, "description must be less than 512 characters")],
    )
    submit = SubmitField("Submit")

    def validate_description(self, description):
        if len(description.data) > 512:
            raise ValidationError("Description must be less than 512 characters")
        return True
