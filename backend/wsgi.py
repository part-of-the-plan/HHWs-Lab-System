"""Gunicorn / 生产 WSGI 入口。

本地开发仍用 run.py（带 debug 自动重载）。
生产由 Gunicorn 加载本文件里的 app 对象：
    gunicorn -c gunicorn.conf.py wsgi:app
FLASK_ENV=production 时 create_app() 自动选 ProductionConfig。
"""
from app import create_app

app = create_app()
