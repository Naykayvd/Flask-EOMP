import hmac
import sqlite3
import datetime
from flask_mail import Mail, Message
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS


class User(object):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password


def fetch_users():
    with sqlite3.connect('point_of_sale.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            print(data)
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


def init_user_table():
    conn = sqlite3.connect('point_of_sale.db')
    print("Opened database")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "email TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("Created table")
    conn.close()


def init_product_prices():
    with sqlite3.connect('point_of_sale.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "product TEXT NOT NULL,"
                     "price INTEGER NOT NULL,"
                     "date_time TEXT NOT NULL)")
    print("product table created successfully.")


init_user_table()
init_product_prices()

users = fetch_users()

email_table = {u.email: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(email, password):
    user = email_table.get(email, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'nahvandiemen@gmail.com'
app.config['MAIL_PASSWORD'] = 'N@#umvd98'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
CORS(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('point_of_sale.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "email,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, email, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
            if request.method == 'POST':
                msg = Message('Confirmation email', sender='nahvandiemen@gmail.com', recipients=[email])
                msg.body = "You successfully registered this email serves as confirmation"
                mail.send(msg)
                return "Send email"


@app.route('/product-page', methods=["POST"])
@jwt_required()
def products():
    response = {}

    if request.method == "POST":
        product = request.form['product']
        price = request.form['price']
        date_time = datetime.datetime.now()

        with sqlite3.connect('point_of_sale.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products("
                           "product,"
                           "price,"
                           "date_time) VALUES(?, ?, ?)", (product, price, date_time))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "product added"
        return response


@app.route('/get-products/', methods=["GET"])
def get_products():
    response = {}
    with sqlite3.connect("point_of_sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")

        items = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = items
    return response


@app.route("/delete product/<int:product_id>")
@jwt_required()
def delete_product(product_id):
    response = {}
    with sqlite3.connect("point_of_sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=" + str(product_id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "product deleted"
    return response


@app.route('/edit-post/<int:product_id>/', methods=["PUT"])
@jwt_required()
def edit_product(product_id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('point_of_sale.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("product") is not None:
                put_data["product"] = incoming_data.get("product")
                with sqlite3.connect('point_of_sale') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET product=? WHERE id=?", (put_data["product"], product_id))
                    conn.commit()
                    response['message'] = "Updated"
                    response['status_code'] = 200
            if incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')
                with sqlite3.connect('point_of_sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET price =? WHERE id=?", (put_data["price"], product_id))
                    conn.commit()
                    response['price'] = "Price adjusted"
                    response['status_code'] = 200
    return response


@app.route('/get-product/<int:product_id>/', methods=["GET"])
def get_item(product_id):
    response = {}

    with sqlite3.connect("point_of_sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id=" + str(product_id))

        response["status_code"] = 200
        response["description"] = "product added"
        response["data"] = cursor.fetchone()

    return jsonify(response)


if __name__ == '__main__':
    app.run()
