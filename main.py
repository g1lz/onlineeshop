import os
from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from data import db_session
from data.form.login_form import LoginForm
from data.form.products_form import ProductsForm
from data.form.purchase_form import PurchaseForm
from data.form.register_form import RegisterForm
from data.model.user import User
from data.model.product import Product
from data.model.purchase import Purchase

app = Flask(__name__)
app.config['UPLOAD_DIR'] = 'static/images'
app.config['SECRET_KEY'] = 'secret_key'
db_session.global_init('db/blogs.db')
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def index_page():
    db_sess = db_session.create_session()
    products = db_sess.query(Product)
    return render_template('index.html', products=products)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('user/login.html', message='Неправильный логин или пароль',
                               form=form)
    return render_template('user/login.html', title='Авторизация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('user/register.html', title='Регистрация', form=form,
                                   message='Пароли не совпадают')
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('user/register.html', title='Регистрация', form=form,
                                   message='Такой пользователь уже есть')
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('user/register.html', title='Регистрация', form=form)


@app.route('/products', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = Product()

        file = form.product_img.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_DIR'], filename))

        products.title = form.title.data
        products.content = form.content.data
        products.price = form.price.data
        products.product_img = os.path.join(app.config['UPLOAD_DIR'], filename)

        current_user.products.append(products)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('product/products.html', title='Добавление товара', form=form)


@app.route('/products/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_products(id):
    form = ProductsForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        products = db_sess.query(Product).filter(Product.id == id, Product.user == current_user
                                                 ).first()
        if products:
            form.title.data = products.title
            form.content.data = products.content
            form.price.data = products.price
        else:
            return render_template('error/404.html')

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        products = db_sess.query(Product).filter(Product.id == id, Product.user == current_user
                                                 ).first()
        file = form.product_img.data
        filename = secure_filename(file.filename)
        if filename not in app.config['UPLOAD_DIR']:
            file.save(os.path.join(app.config['UPLOAD_DIR'], filename))

        if products:
            products.title = form.title.data
            products.content = form.content.data
            products.price = form.price.data
            products.product_img = os.path.join(app.config['UPLOAD_DIR'], filename)
            db_sess.commit()
            return redirect('/')
        else:
            return render_template('error/404.html')
    return render_template('product/products.html', title='Редактирование товара', form=form)


@app.route('/products_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def products_delete(id):
    db_sess = db_session.create_session()
    products = db_sess.query(Product).filter(Product.id == id, Product.user == current_user
                                             ).first()
    if products:
        db_sess.delete(products)
        db_sess.commit()
    else:
        return render_template('error/404.html')
    return redirect('/')


@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    form = PurchaseForm()
    db_sess = db_session.create_session()
    product_id = request.args.get('product_id')
    product = db_sess.query(Product).get(product_id)

    if product is None:
        return render_template('error/404.html')

    if form.validate_on_submit():
        purchase = Purchase()

        purchase.receiver_name = form.receiver_name.data
        purchase.address = form.address.data
        purchase.product_id = product.id

        current_user.purchase.append(purchase)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('purchase/purchase.html', title='Оформление заказа', form=form)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error/404.html'), 404


@app.errorhandler(401)
def authorization_required(error):
    return render_template('error/401.html'), 401


if __name__ == "__main__":
    app.run(debug=True)
