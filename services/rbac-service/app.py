from flask import Flask, jsonify
import os
app = Flask(__name__)


@app.route('/')
def index():
    resp = {"msg": "ok", "serviceName": "rbac-service"}
    return jsonify(resp)


@app.route('/liveness')
def healthx():
    resp = {"msg": "ok"}
    return jsonify(resp)

@app.route('/user/<user_id>')
def get_user(user_id):
    resp = {"permissions": "superAdmin", "id": user_id}
    return jsonify(resp)


@app.route('/readiness')
def healthz():
    resp = {"msg": "ok"}
    return jsonify(resp)



app.run(host='0.0.0.0', port=os.getenv("FLASK_PORT", 8090))
