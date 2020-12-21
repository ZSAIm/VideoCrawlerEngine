
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField
from wtforms.validators import DataRequired


class NewSubmitForm(FlaskForm):
    urls = TextAreaField('urls', validators=[DataRequired()])


class SettingsConfigForm(FlaskForm):
    tempdir = StringField('tempdir', validators=[DataRequired()])
    storage_dir = StringField('storage_dir', validators=[DataRequired()])
