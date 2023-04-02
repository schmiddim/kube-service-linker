from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    resp = {"msg": "ok", "serviceName": "user-service"}
    return jsonify(resp)


@app.route('/liveness')
def healthx():
    resp = {"msg": "ok"}
    return jsonify(resp)


@app.route('/readiness')
def healthz():
    resp = {"msg": "ok"}
    return jsonify(resp)



app.run(host='0.0.0.0', port=8080)
