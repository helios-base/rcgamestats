# from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField, BooleanField
from wtforms.validators import DataRequired, Optional, Regexp, Length, ValidationError


class TeamUploadForm(FlaskForm):
    """
    Team upload form input class
    """

    # def __init__(self, *args, **kwargs):
    #     super(TeamUploadForm, self).__init__(*args, **kwargs)
    #     self.version.data = datetime.now().strftime("%Y%m%d-%H%M%S")

    team_name = StringField(
        "Team Name(*): ",
        validators=[
            DataRequired("team name is required"),
            Length(4, 32, "team name must be between 4 and 32 characters"),
            Regexp(r"^(?!-)[a-zA-Z0-9_-]+$", message="team name must be alphanumeric"),
        ],
    )
    version = StringField(
        "Version: (Empty for auto-generated with timestamp)",
        validators=[
            # DataRequired("team version is required"),
            Optional(),
            Length(0, 16, "team version must be less than 16 characters"),
            Regexp(
                r"^(?!-)[a-zA-Z0-9_-]+$", message="team version must be alphanumeric"
            ),
        ],
    )
    synch_mode = BooleanField("Support synch_mode: ", default=True, validators=[])
    archive_file = FileField(
        "Archive File(*): ", validators=[DataRequired("team archive is required")]
    )
    description = TextAreaField(
        "Description: ", validators=[Length(0, 512, "description must be less than 512 characters")]
    )
    submit = SubmitField("Submit")

    def validate_archive_file(self, archive_file):
        """
        Validate the team archive file extension
        """
        print("validate_archive_file", archive_file.data)
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
