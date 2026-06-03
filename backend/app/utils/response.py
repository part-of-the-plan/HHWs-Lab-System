"""统一响应格式封装：所有接口返回 {code, message, data}。"""
from flask import jsonify


def success(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})


def error(message="error", code=1, http_status=400):
    resp = jsonify({"code": code, "message": message, "data": None})
    resp.status_code = http_status
    return resp
