import hashlib
import os

from flask import Flask, request, jsonify
import ydb
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)


def get_config():
    endpoint = os.getenv("endpoint")
    database = os.getenv("database")
    if endpoint is None or database is None:
        raise AssertionError("Нужно указать обе переменные окружения")
    credentials = ydb.iam.ServiceAccountCredentials.from_file('serverless-shortener.sa')
    return ydb.DriverConfig(endpoint, database, credentials=credentials)


def execute(config, query, params):
    with ydb.Driver(config) as driver:
        try:
            driver.wait(timeout=10)
        except TimeoutError:
            print("Connect failed to YDB")
            print("Last reported errors by discovery:")
            print(driver.discovery_debug_details())
            return None

        session = driver.table_client.session().create()
        prepared_query = session.prepare(query)

        return session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query,
            params,
            commit_tx=True
        )


@app.route('/api/ads', methods=['GET'])
def get_ads():
    config = get_config()
    query = "SELECT * FROM ads;"
    result_set = execute(config, query, {})
    if not result_set:
        return jsonify([])

    return jsonify([{'id': row.id, 'ad': row.ad} for row in result_set[0].rows])


@app.route('/api/ads', methods=['POST'])
def post_ad():
    ad = request.json.get('ad')
    if not ad:
        return 'Bad Request', 400

    config = get_config()
    query = """
        DECLARE $id AS Utf8;
        DECLARE $ad AS Utf8;

        UPSERT INTO ads (id, ad) VALUES ($id, $ad);
        """
    params = {'$id': hashlib.sha256(ad.encode('utf8')).hexdigest()[:6], '$ad': ad}
    execute(config, query, params)

    return jsonify({'message': 'Created', 'ad': ad}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
