from flask import request, Flask, render_template, url_for, redirect, send_from_directory, g, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from User import User
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
from DataBase import DataBase
import psycopg2
from config import host, user, password, db_name



UPLOAD_FOLDER = 'static/photos/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
SECRET_KEY = 'hard to guess string'

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# conn = sqlite3.connect("identifier.sqlite", check_same_thread=False)
# cursor = conn.cursor()
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
menu = [{'name': 'Товары', 'url': 'goods'},
        {'name': 'Заказы', 'url': 'orders'},
        {'name': 'Возвраты', 'url': 'refunds'},
        {'name': 'Списания', 'url': 'writeoff'},
        {'name': 'Оприходования', 'url': 'postings'},
        {'name': 'Инвентаризации', 'url': 'inventory'},
        {'name': 'Покупатели', 'url': 'customers'},
]

dbase = None
login_manager = LoginManager(app)

# переадресация для неавторизованных
login_manager.login_view = 'login'
login_manager.login_message = "Авторизируйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"

@login_manager.user_loader
def load_user(user_id):
    return User().fromdB(user_id, dbase)

def get_db():
    """ Возвращает объект соединения с БД"""
    db = getattr(g, '_database', None)
    if db is None:
        try:
            db = g._database = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=db_name)
        except:
            print("DB error connection")
    return db


@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = DataBase(db)


@app.teardown_appcontext
def close_connection(exception):
    """Закрывает соединение с с БД"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/goods/', methods=['GET', 'POST'])
@login_required
def goods():
    if request.method == 'POST':
        text_for_search = request.form.get('search_text_field')
        print(text_for_search)
    table = dbase.get_items_preview()
    print(table)
    return render_template('goods.html', menu=menu, table=table)


@app.route('/orders/', methods=['GET','POST'])
@login_required
def orders():
    orders_list = dbase.get_order_list()
    if request.method == 'POST':
        new_statuses = request.form.getlist('select[]')
        dbase.update_orders_statuses(new_statuses)
        return redirect(url_for('orders'))
    return render_template('orders.html', menu=menu, orders= orders_list)


@app.route('/orders/<order_numb>/', methods=['GET','POST'])
@login_required
def order_number(order_numb):
    order = dbase.get_order_by_number(int(order_numb))
    check_change_status = order[0][4]
    if request.method == "POST":
        status = request.form.get("select")
        barcodes = request.form.getlist("barcodes[]")
        amounts = request.form.getlist("amounts[]")
        prices = request.form.getlist("prices[]")
        customer = request.form.get("customer")
        if check_change_status == "new" and status != "new":
            dbase.make_ship(order_numb, status, barcodes, amounts, prices, customer, "order")
        else:
            dbase.make_ship(order_numb, status, barcodes, amounts, prices, customer, "reload")
        return redirect(f"/orders/{order_numb}")
    return render_template("order_number.html", menu=menu, order_list=order)


@app.route('/refunds/')
@login_required
def refunds():
    refunds_list = dbase.get_refunds_list()
    return render_template('refunds.html', menu=menu, refunds=refunds_list)

@app.route('/refunds/<ref_numb>/')
@login_required
def one_refund(ref_numb):
    print(ref_numb, type(ref_numb))
    refund = dbase.get_one_refund(int(ref_numb))
    return render_template('refund_number.html', menu=menu, refund=refund)



@app.route('/writeoff/')
@login_required
def writeoff():
    return render_template('writeoff.html', menu=menu)


@app.route('/postings/')
@login_required
def postings():
    return render_template('postings.html', menu=menu)


@app.route('/inventory/')
@login_required
def inventory():
    inv_list = dbase.get_invent_preview()

    return render_template('inventory.html', menu=menu, inv_list=inv_list)

@app.route('/inventory/new_inventory/', methods=["GET","POST"])
@login_required
def new_inventory():
    bc_list = dbase.get_bc_list()
    if request.method == "POST":
        bars = request.form.getlist("barcodes[]")
        us = current_user.get_id()
        res = dbase.make_inventory(bars, us)
        if res:
            flash("Инвентаризация проведена успешно")
        else:
            flash("Возникла ошибка, проверьте введенные данные")
    return render_template('new_inventory.html', menu=menu, bc_list=bc_list)

@app.route('/customers/')
@login_required
def customers():
    cust = dbase.get_customers()
    return render_template('customers.html', menu=menu, cust_list=cust)



@app.route('/customers/add_cust/', methods=["GET","POST"])
@login_required
def add_cust():
    if request.method=="POST":
        name = request.form.get("cust_name")
        contact = request.form.get("contact")
        r = dbase.add_customers(name,contact)
        if r:
            flash("Успешно добавлен покупатель")
        else:
            flash("Ошибка при добавлении покупателя")
    return render_template('add_cust.html', menu=menu)


@app.route('/')
@login_required
def stand():  # put application's code here
    # print(url_for('hello_world'))
    return render_template('menubar.html', menu=menu)


@app.route('/goods/<artic>/add_photo', methods=['GET','POST'])
@login_required
def add_photo(artic):
    c = dbase.get_colors_by_art(artic)
    colors = [[i, [j[1] for j in c if j[0] == i]] for i in set([x[0] for x in c])]
    if request.method == "POST":
        dataGet = {}
        try:
            dataGet = request.get_json(force=True)
        except:
            pass
        # удаление фотографии
        if "photo_to_delete" in dataGet:
            photo_for_delete = str(dataGet["photo_to_delete"]).replace("del-b-","")
            dbase.delete_photo(photo_for_delete)
            file = os.path.join(app.config['UPLOAD_FOLDER'], photo_for_delete)
            os.remove(file)
            dataReply = {'status': 'ok'}
            return jsonify(dataReply)
        else:
            # сохранение новый фотографий
            photos = request.files.getlist("photos")
            paths = [i.filename for i in photos]
            color_for_update = request.form.get("color")
            for file in photos:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    path_to_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    if os.path.exists(path_to_file):
                        continue  # сохранение файлов с одинокавым названием
                    file.save(path_to_file)
                else:
                    flash("Данный тип файла недоступен для загрузки: " + file.filename)
                    paths.remove(file.filename)
            if len(photos) > 0:
                dbase.update_photos_for_art_and_color(artic, color_for_update, paths)
            return redirect(f"/goods/{artic}/add_photo")
    return render_template('add_photo.html', menu=menu, colors_by_art=colors, artic=artic)

@app.route('/goods/add_new/', methods=['GET', 'POST'])
@login_required
def add_new():

    if request.method == 'POST':
        name = request.form.get('name')
        vendor_code = request.form.get('vendor_code')
        brand = request.form.get('brand')
        description = request.form.get('description')
        material = request.form.get('material')
        first_price = request.form.get('first-price')
        selling_price = request.form.get('selling-price')
        discount_price = request.form.get('discount-price')

        size = request.form.getlist('size[]')
        color = request.form.getlist('color[]')
        amount = request.form.getlist('amount[]')

        country = request.form.get('country')
        category = request.form.get('category')
        type = request.form.get('type')
        tnvd = request.form.get('tnvd')
        weight = request.form.get('weight')
        packtype = request.form.get('packtype')
        packsize = request.form.get('packsize')
        gender = request.form.get('gender')
        season = request.form.get('season')

        # name,vendor_code,description,material,first_price,selling_price,discount_price,size,color,amount,country,category,type,tnvd,weight, packtype,packsize,gender,season
        barcode = request.form.getlist('barcode[]')

        # files = request.files.getlist("photos")
        # paths = []
        # for file in files:
        #     if file and allowed_file(file.filename):
        #         filename = secure_filename(file.filename)
        #         path_to_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #         print(path_to_file)
        #         paths.append(path_to_file)
        #         # if os.path.exists(path_to_file):
        #         #     pass # ? сохранение файлов с одинокавым названием
        #         file.save(path_to_file)
        #     else:
        #         print("Данный тип файла недоступен для загрузки")
        # paths = " ".join(paths)
        try:
            dbase.add_item(name, vendor_code, brand, description, material,
                     first_price, selling_price, discount_price, country,
                     category, type, tnvd, weight, packtype, packsize, gender, season)

            dbase.add_item_modif(vendor_code, size, color, amount, barcode)
            flash("Товар успешно сохранен")
        except:
            flash("Не удалось добавить товар, либо модификации")


        # cursor = get_db().cursor()
    # добавление товара в базу данных, добавить полноценную функцию
    #     cursor.execute("INSERT INTO goods(name, vendor_code, description, material, first_price, selling_price, discount_price, country, category, type, tnvd, weight, packtype, packsize, gender, season) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);", (name, vendor_code, description, material, first_price, selling_price, discount_price, country, category, type, tnvd, weight, packtype, packsize, gender, season))
    #     get_db().commit()
        ## cursor.close()
        ## get_db().close()

        # print(name + '\n' + vendor_code + '\n' + description + '\n')


        return redirect(url_for('add_new'))
    return render_template('add_new.html', menu=menu)


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/goods/<artic>/', methods=['GET','POST'])
@login_required
def goods_art(artic):
    item = dbase.get_item(artic)
    m = dbase.get_modif(artic)
    print(m)
    photo = url_for('static', filename="photos/"+dbase.get_one_photo(artic)[0])
    if request.method=="POST":
        name = request.form.get('name')
        vendor_code = request.form.get('vendor_code')
        brand = request.form.get('brand')
        print(brand)
        description = request.form.get('description')
        material = request.form.get('material')
        first_price = request.form.get('first-price')
        selling_price = request.form.get('selling-price')
        discount_price = request.form.get('discount-price')

        size = request.form.getlist('size[]')
        color = request.form.getlist('color[]')
        amount = request.form.getlist('amount[]')
        barcode = request.form.getlist('barcode[]')

        country = request.form.get('country')
        category = request.form.get('category')
        type = request.form.get('type')
        tnvd = request.form.get('tnvd')
        weight = request.form.get('weight')
        packtype = request.form.get('packtype')
        packsize = request.form.get('packsize')
        gender = request.form.get('gender')
        season = request.form.get('season')

        res1 = dbase.update_item(name, vendor_code, artic, brand, description, material,
                                         first_price, selling_price, discount_price, country,
                                         category, type, tnvd, weight, packtype, packsize, gender, season)

        res2 = dbase.update_item_modif(vendor_code, size, color, amount, barcode)
        if res1 and res2:
            flash("Данные успешно обновлены")
            return redirect(f"/goods/{vendor_code}/")

        else:
            flash("Ошибка при обновлении данных")
    return render_template("item.html", menu=menu, item=item, mods=m, photo_src=photo)




# вход
@app.route('/login/', methods = ["POST","GET"])
def login():
    if current_user.is_authenticated:
        try:
            if current_user.get_role()=="staff":
                return redirect(url_for('profile'))
            if current_user.get_role()=="admin":
                return redirect(url_for('admin_profile'))
        except:
            return redirect(url_for('login'))

    if request.method == "POST":
        user = dbase.get_user_by_email(request.form['email'])
        if user and check_password_hash(user[5], request.form['password']):
            user_login = User().create(user)
            remainme = True if request.form.get('remainme') else False
            login_user(user_login, remember=remainme)
            return redirect(request.args.get('next') or url_for('profile'))
        flash("Неверная пара логин/пароль", "error")

    return render_template('login.html', menu=menu)



# регистрация
@app.route('/singup/', methods=["POST", "GET"])
def singup():
    if dbase.has_admin():
        pass
        # return redirect(url_for("profile"))
    else:
        if request.method == "POST":
            if len(request.form['email']) > 5 and len(request.form['name']) > 4 and len(request.form['password'])>5 and len(request.form['phone']) >5:
                hash = generate_password_hash(request.form['password'])
                res_singup = dbase.add_admin(request.form['email'],request.form['name'],request.form['phone'],hash)
                if res_singup:
                    flash("Регистрация успешно выполнена","success")
                    return redirect(url_for("login"))
                else:
                    flash("Ошибка при добавлении в БД", "error")
            else:
                flash("Неверно заполнены поля", "error")
    return render_template('singup.html', menu=menu)


@app.route('/logout/')
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile/', methods=['GET', 'POST'])
@login_required
def profile():
    try:
        if current_user.get_role() == "admin":
            return redirect(url_for("admin_profile"))
        if request.method == 'POST':
            name = str(request.form.get('username'))
            phone = str(request.form.get('phone'))
            email = str(request.form.get('email'))

            res = dbase.update_user_info(current_user.get_id(),name,email, phone)
            if res:
                flash("Информация успешно обновлена")
                # return render_template('profile.html', menu=menu)
                # redirect(url_for('profile'))
            else:
                flash("Ошибка при обновлении информации")
        return render_template('profile.html', menu=menu)
    except:
        return redirect(url_for('singup'))


@app.route('/admin_profile/', methods=['GET', 'POST'])
@login_required
def admin_profile():
    if request.method == 'POST':
        name = str(request.form.get('username'))
        phone = str(request.form.get('phone'))
        email = str(request.form.get('email'))
        res = dbase.update_user_info(current_user.get_id(), name, email, phone)
        if res:
            flash("Информация успешно обновлена")
            # return render_template('profile.html', menu=menu)
            # redirect(url_for('profile'))
        else:
            flash("Ошибка при обновлении информации")
    return render_template('admin_profile.html', menu=menu)


@app.route("/add_staff/", methods=['GET', 'POST'])
def add_staff():
    if request.method == "POST":
        if len(request.form['email']) > 5 and len(request.form['name']) > 4 and len(request.form['password'])>5 and len(request.form['phone']) >5:
            hash = generate_password_hash(request.form['password'])
            res_singup = dbase.add_user(request.form['email'],request.form['name'],request.form['phone'],hash)
            if res_singup:
                flash("Регистрация успешно выполнена","success")
                return redirect(url_for("goods"))
            else:
                flash("Ошибка при добавлении в БД", "error")
        else:
            flash("Неверно заполнены поля","error")
    return render_template('add_staff.html', menu=menu)



@app.route("/orders/new_order/", methods=['GET', 'POST'])
@login_required
def new_order():
    bc_list = dbase.get_bc_list()
    print(bc_list)
    if request.method=="POST":
        barcodes = request.form.getlist("barcodes[]")
        amount = request.form.getlist("amount[]")
        selling_price = request.form.getlist("selling-price[]")
        customer = request.form.getlist("customer")
        print(barcodes)
        try:
            if dbase.add_order(barcodes,amount,selling_price, customer):
                flash("Заказ успешно создан")
            else:
                flash("Ошибка, проверьте введенные данные")
        except:
            flash("Ошибка записи заказа в БД")
    return render_template("new_order.html", menu=menu, bc_list=bc_list )

@app.route("/refunds/new_refund/", methods=["GET","POST"])
@login_required
def new_refund():
    bc_list = dbase.get_bc_list()
    if request.method == "POST":
        barcodes = request.form.getlist("barcodes[]")
        customer = request.form.getlist("customer")
        print(barcodes)
        try:
            if dbase.add_refund(barcodes, customer):
                flash("Возврат успешно добавлен")
            else:
                flash("Ошибка, проверьте введенные данные")
        except:
            flash("Ошибка записи заказа в БД")
    return render_template("new_refund.html", menu=menu, bc_list=bc_list)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def check_valid(s):
    if s is not None:
        s = str(s)
        if len(s) > 0:
            return s
        else:
            print("1")
            raise ValueError("Неверный ввод данных")
    else:
        print("2")
        raise ValueError("Неверный ввод данных")

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
