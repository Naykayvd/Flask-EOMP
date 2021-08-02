import hmac
import sqlite3
import requests

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS


class User(object):
    def __init__(self, phone, email, password):
        self.phone = phone
        self.email = email
        self.password = password


def fetch_users():
    with sqlite3.connect('point_of_sale.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4]))
    return new_data


users = fetch_users()


def init_user_table():
    conn = sqlite3.connect('point_of_sale.db')
    print("Opened database")

    conn.execute("CREATE TABLE IF NOT EXISTS user(phone_number INTEGER PRIMARY KEY,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "email TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("Created table")
    conn.close()


def init_product_prices():
    with sqlite3.connect('point_of_sale.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products(product_price INTEGER,"
                     "product_name TEXT NOT NULL,"
                     "date purchased TEXT NOT NULL)")
    print("product table created successfully.")


init_user_table()
init_product_prices()

email_table = {u.email: u for u in users}
phone_table = {u.phone: u for u in users}


def authenticate(email, password):
    user = email_table.get(email, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def user_phone(payload):
    phone_number = payload['user_phone']
    return phone_table.get(phone_number, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
CORS(app)

