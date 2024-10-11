import json
from flask import Response
from datetime import datetime


def jsonify_response(data, status_code=200):
    response_json = json.dumps(data, ensure_ascii=False)
    return Response(response_json, status=status_code, mimetype='application/json')


def to_iso8601(date: datetime):
    return date.strftime('%Y-%m-%dT%H:%M:%S.') + f'{date.microsecond // 1000:03d}' + 'Z'


def to_datetime(iso: str):
    return datetime.fromisoformat(iso.replace('Z', '+00:00'))