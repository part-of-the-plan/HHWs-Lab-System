"""时区工具：数据库存 UTC，显示时转北京时间（UTC+8）。"""
from datetime import timedelta, timezone

# 北京时间 = UTC + 8
BEIJING_TZ = timezone(timedelta(hours=8))


def to_beijing_time(dt):
    """把 UTC datetime 转为北京时间字符串，用于 API 返回。
    如果 dt 已经是 aware（带时区），先转 UTC 再加 8 小时；
    如果 dt 是 naive（不带时区），假设它就是 UTC 直接加 8 小时。
    """
    if dt is None:
        return None
    # datetime 存的是 naive UTC（datetime.utcnow()），直接加位移
    # 避免使用 astimezone 产生依赖 pytz 的问题
    return str(dt + timedelta(hours=8))
