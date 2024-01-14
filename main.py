from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route('/api', methods=['GET'])
def api():
    name = request.args.get('name', 'World')
    return jsonify({'message': f'Hello, {name}!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
