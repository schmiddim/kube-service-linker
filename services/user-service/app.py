from flask import Flask, jsonify
import os
from flaskext.mysql import MySQL
app = Flask(__name__)



mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = os.getenv('MYSQL_DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv('MYSQL_DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.getenv('MYSQL_DATABASE_DB')
app.config['MYSQL_DATABASE_HOST'] = os.getenv('MYSQL_DATABASE_HOST')
mysql.init_app(app)


@app.route('/')
def index():
    resp = {"msg": "ok", "serviceName": "user-service"}
    return jsonify(resp)


@app.route('/user/<user_id>')
def get_user(user_id):
    resp = {"username": "michael", "firstname": "Michael", "lastname": "Schmitt", "id": user_id}
    return jsonify(resp)


@app.route('/liveness')
def healthx():
    conn = mysql.connect()
    resp = {"msg": "ok"}
    return jsonify(resp)


@app.route('/readiness')
def healthz():
    conn = mysql.connect()
    resp = {"msg": "ok"}
    return jsonify(resp)


app.run(host='0.0.0.0', port=os.getenv("FLASK_PORT", 8080))
