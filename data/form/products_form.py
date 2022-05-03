from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from flask_wtf.file import FileField
from wtforms.validators import DataRequired


class ProductsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    price = IntegerField('Цена', validators=[DataRequired()])
    content = TextAreaField('Содержание', validators=[DataRequired()])
    product_img = FileField('Изображение', validators=[DataRequired()])
    submit = SubmitField('Создать')