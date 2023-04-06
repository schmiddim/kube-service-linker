from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/', methods=['POST'])
def process_post_request():
    data = request.get_json()
    print("Erhaltene Daten:", data)
    return jsonify({'result': "ok", "recived":data})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)
