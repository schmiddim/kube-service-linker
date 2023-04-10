import logging

from flask import Flask, request, jsonify
from modules.kube import load_config
from modules.logic import analyze_requirements
from modules.crds import create_service_requirement_crd

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
)
load_config()
create_service_requirement_crd()


@app.route('/', methods=['POST'])
def process_post_request():
    data = request.get_json()
    print(data)
    analyze_requirements(data)

    return jsonify({'result': "ok", "recived": data})


if __name__ == '__main__':
    load_config()
    app.run(debug=True, host='0.0.0.0', port=9000)
