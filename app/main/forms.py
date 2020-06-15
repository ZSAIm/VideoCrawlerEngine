
from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired


class NewSubmitForm(FlaskForm):
    urls = TextAreaField('urls', validators=[DataRequired()])



