"""
随机数据生成工具
"""
import random
import string
import uuid


def random_email(domain="dify.ai", prefix="auto"):
    """
    生成随机邮箱，格式：{prefix}_{random}@{domain}。
    默认 prefix=auto、domain=dify.ai，例如 auto_a1b2c3d4@dify.ai。
    """
    r = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{r}@{domain}"


def random_email_with_uuid(domain="dify.ai", prefix="auto"):
    """
    使用 uuid 生成随机邮箱，格式：{prefix}_{uuid_hex}@{domain}。
    更不易重复，适合单次运行内唯一标识。
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}@{domain}"

def random_name(domain="test", prefix="auto"):
    r = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{r}_{domain}"
