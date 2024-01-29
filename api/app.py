import json
from datetime import datetime, timedelta
from flask import Flask, Response, make_response
from api.xamanager import Xamanager

app = Flask(__name__)
manager = Xamanager()
time_stamp = datetime.now()


@app.route('/api/v1.0/xamarin/version/<string:platform>', methods=['GET'])
def xamarin(platform):
    global time_stamp

    if platform == '' or platform not in manager.platforms:
        return Response(json.dumps({'error': 'Platform not found'}), mimetype='application/json', status=404)

    # look for new versions
    if datetime.now() - time_stamp > timedelta(minutes=120):
        manager.search_new_versions()
        time_stamp = datetime.now()

    # return the data
    response = make_response(manager.get_current_version(platform))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/api/v1.0/xamarin/version/<string:platform>/all', methods=['GET'])
def all_versions(platform):
    global time_stamp

    if platform == '' or platform not in manager.platforms:
        return Response(json.dumps({'error': 'Platform not found'}), mimetype='application/json', status=404)

    # look for new versions
    if datetime.now() - time_stamp > timedelta(minutes=120):
        manager.search_new_versions()
        time_stamp = datetime.now()

    response = make_response(manager.dumps[platform])
    response.headers['Content-Type'] = 'application/json'
    return response


if __name__ == '__main__':
    app.run()
