"""统一响应格式封装：所有接口返回 {code, message, data}。"""
from flask import jsonify


def success(data=None, message="ok"):
    return jsonify({"code": 0, "message": message, "data": data})


def error(message="error", code=1, http_status=400):
    resp = jsonify({"code": code, "message": message, "data": None})
    resp.status_code = http_status
    return resp


def paginate(query, schema, page=1, per_page=10):
    """分页查询 + 统一响应格式。用法：return paginate(User.query, User.to_dict_simple)

    返回：{ code:0, message:"ok", data:{ items:[...], total:156, page:1, per_page:10 } }
    """
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [schema(item) for item in pagination.items]
    return success({
        "items": items,
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
    })
