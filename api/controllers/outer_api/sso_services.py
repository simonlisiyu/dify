# controllers/outer_api/sso_api.py

import logging
import secrets
import jwt
from flask import request
from flask_restful import Resource, reqparse
from services.account_service import AccountService, RegisterService
from constants.languages import languages

logger = logging.getLogger(__name__)

# 使用与outer_services.py相同的token验证配置
CLIENTS_TOKENS = {"haizhi": "haizhi", "client2": "test"}
CLIENT_SECRET = "haizhi_secret"


class SSOLoginApi(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("authorization", type=str, location="headers",
                            required=True, help="Authorization header is required for authentication.")
        parser.add_argument('username', type=str, required=True, location='json')
        parser.add_argument('role', type=str, required=False, default='normal', location='json')
        parser.add_argument('tenant_id', type=str, required=True, location='json')
        args = parser.parse_args()

        # 验证服务间token
        if not validate_token(args['authorization'], CLIENT_SECRET, CLIENTS_TOKENS):
            return {"error": "Unauthorized"}, 401

        username = args['username']
        tenant_id = args['tenant_id']
        role = args['role']

        try:
            # 查找用户是否存在
            account = AccountService.get_user_through_email(username)

            # 如果用户不存在，创建新用户
            if account is None:
                # 生成随机密码
                random_password = secrets.token_urlsafe(12)  # 使用secrets模块直接生成随机密码

                account = RegisterService.register(
                    email=username,
                    tenant_id=tenant_id,
                    name=username,
                    password=random_password,
                    role=role if role else 'normal',
                    language=languages[0]  # 默认使用第一个支持的语言
                )

            # 执行登录
            token_pair = AccountService.login(
                account=account,
                ip_address=request.remote_addr
            )

            # 构建跳转URL（添加token到URL参数）
            redirect_url = f"{request.host_url}console?token={token_pair.access_token}"

            return {
                "result": "success",
                "data": {
                    "redirect_url": redirect_url,
                    "token": token_pair.model_dump()
                }
            }

        except Exception as e:
            logger.error(f"SSO login failed for user {username}: {str(e)}")
            return {"error": str(e)}, 500

def validate_token(authorization, client_secret, client_dict):
    """验证服务间token的函数，与outer_services.py中相同"""
    if not authorization:
        return False

    try:
        token_type, token = authorization.split(None, 1)
    except ValueError:
        logger.warning("Invalid authorization header format")
        return False

    if token_type.lower() == 'bearer':
        try:
            decoded_token = jwt.decode(token, client_secret, algorithms=['HS256'])
            if 'client_id' in decoded_token:
                client_id = decoded_token['client_id']
                if client_id in client_dict:
                    logger.info(f"token={token} success")
                    return True
                else:
                    logger.warning(f"client_id={client_id} failed")
            else:
                logger.warning("client_id is not exist.")
        except jwt.InvalidTokenError:
            logger.warning("jwt.decode failed.")
    else:
        logger.warning("token type is not Bearer.")

    return False