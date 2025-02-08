from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


class GroupCreateForm(FlaskForm):
    """
    グループ作成用入力クラス
    """

    # グループ名：文字列入力
    group_name = StringField('グループ名：')
    # ボタン
    submit = SubmitField('作成')