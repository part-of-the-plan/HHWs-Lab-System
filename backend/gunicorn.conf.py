# Gunicorn 生产配置 —— 与 wsgi.py 配套
# 启动： gunicorn -c gunicorn.conf.py wsgi:app
# 由 systemd 托管（见 deploy/lab-backend.service）

import multiprocessing

# 只监听本机回环：外部一律走 Nginx 反代，Gunicorn 不直接对公网暴露
bind = "127.0.0.1:5000"

# worker 数：经验公式 2*CPU+1。2核机器约 5 个；按需在 .env 调
workers = int(multiprocessing.cpu_count() * 2 + 1)
worker_class = "sync"           # 纯 Flask 同步应用，sync 足够
threads = 2

timeout = 60                    # 单请求最长 60s，超时杀 worker
graceful_timeout = 30
keepalive = 5

max_requests = 1000             # 处理 1000 个请求后重启 worker，防内存泄漏
max_requests_jitter = 100       # 加随机抖动，避免 worker 同时重启

# 日志：交给 systemd/journald 收集，输出到标准流
accesslog = "-"
errorlog = "-"
loglevel = "info"

proc_name = "lab-backend"
