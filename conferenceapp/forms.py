from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField,TextAreaField,PasswordField

from wtforms.validators import DataRequired, Email,Length

class Loginform(FlaskForm):
    username=StringField('Your email',validators=[DataRequired(),Email()])
    pwd=PasswordField('Enter password:')
    loginbtn=SubmitField('Login')

class ContactForm(FlaskForm):
    name=StringField("Your Fullname",validators=[DataRequired()])
    email=StringField("Your email",validators=[DataRequired(),Email()])
    message=TextAreaField("Your Comment",validators=[DataRequired()])
    btn=SubmitField("Send")