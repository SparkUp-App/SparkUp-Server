import json
from flask import Response


def jsonify_response(data, status_code=200):
    response_json = json.dumps(data, ensure_ascii=False)
    return Response(response_json, status=status_code, mimetype='application/json')
