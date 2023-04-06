import json

from flask import Flask, jsonify
import requests as r
import os

app = Flask(__name__)

user_endpoint = os.getenv("ENDPOINT_USER_SERVICE", "http://localhost:8080")
rbac_endpoint = os.getenv("ENDPOINT_RBAC_SERVICE", "http://localhost:8090")


@app.route('/')
def index():
    try:
        resp_user = r.get("{}/user/1".format(user_endpoint))
        if resp_user.status_code != 200:
            user_data = "Error: Return Code RBAC:{}".format(resp_user.status_code)
        else:
            user_data = resp_user.json()
    except r.exceptions.RequestException as e:
        print("Error getting {}: {}".format(user_endpoint, e))
        user_data = {"error": "unable to get data {}".format(e)}

    try:
        resp_rbac = r.get("{}/user/1".format(rbac_endpoint))
        if resp_rbac.status_code != 200:
            rbac_data = "Error: Return Code RBAC:{}".format(resp_rbac.status_code)
        else:
            rbac_data = resp_rbac.json()
    except r.exceptions.RequestException as e:
        print("Error getting {}: {}".format(user_endpoint, e))
        rbac_data = {"error": "unable to get data {}".format(e)}
    resp_user = {"msg": "ok",
                 "serviceName": "homepage-service",

                 "userService": user_data,
                 "rbacService": rbac_data,
                 "endpoints":[user_endpoint, rbac_endpoint]
                 }
    return jsonify(resp_user)


@app.route('/liveness')
def healthx():
    resp = {"msg": "ok"}
    return jsonify(resp)


@app.route('/readiness')
def healthz():
    resp = {"msg": "ok"}
    return jsonify(resp)


app.run(host='0.0.0.0', port=8100)
