import hashlib
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config.settings import settings
from src.utils.logger import logger

security = HTTPBasic(auto_error=False)

# JWT 配置
JWT_SECRET_KEY = getattr(settings, "jwt_secret_key", "dev-secret-key-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 1天


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配存储的哈希地址"""
    if ":" not in hashed_password:
        # P2-FIX: 向后兼容但加日志警告，提醒升级到哈希密码
        logger.warning(
            "⚠️ verify_password 退化为明文比较 — 请在 .env 中配置 ADMIN_PASSWORD_HASH "
            "(格式: sha256:<salt>:<hex_digest>) 替代明文 ADMIN_PASSWORD"
        )
        return secrets.compare_digest(plain_password, hashed_password)

    try:
        algo, salt, expected_hash = hashed_password.split(":")
        if algo != "sha256":
            return False

        hash_obj = hashlib.sha256()
        hash_obj.update(f"{salt}{plain_password}".encode())
        actual_hash = hash_obj.hexdigest()

        return secrets.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    """生成 JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_admin(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
    """
    权限校验依赖项：
    1. 优先检查 HTTP Header 的 Authorization: Bearer <JWT>
    2. 兼容旧版的 HTTP Basic Auth
    """
    auth_header = request.headers.get("Authorization")

    # 1. JWT Bearer 验证
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            if username == settings.admin_username:
                return username
        except jwt.PyJWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    # 2. HTTP Basic Auth 验证（兼容旧版 dashboard）
    if credentials:
        stored_password = getattr(settings, "admin_password_hash", None) or settings.admin_password
        if verify_password(credentials.password, stored_password) and secrets.compare_digest(
            credentials.username, settings.admin_username
        ):
            return credentials.username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Basic / Bearer"},
    )
