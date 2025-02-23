import requests
import json
import jsonschema
from configparser import ConfigParser

# 读取配置文件
config = ConfigParser()
config.read('../config.ini')

# 常量定义
BASE_URL = "http://127.0.0.1:5001"
ENDPOINT = "/console/api/directory"
AUTHORIZATION_TOKEN = config.get('API', 'authorization_token')

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": AUTHORIZATION_TOKEN
}


# 请求体（非根目录）
non_root_directory_payload = {
    "name": "new12",
    "type": "app",
    "parent_id": "b22d949f-e158-4905-8c26-8090813943d7"
}

# 返回数据的JSON Schema（创建目录）
response_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "directory_id": {"type": "string"}
    },
    "required": ["message", "directory_id"]
}

# 返回数据的JSON Schema（获取目录树）
get_tree_response_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "dir_tree": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "level": {"type": ["null", "string"]},
                    "parent_id": {"type": "string"},
                    "sub_dir": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "level": {"type": "string"},
                                "parent_id": {"type": "string"},
                                "sub_dir": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "type": {"type": "string"},
                                            "level": {"type": "string"},
                                            "parent_id": {"type": "string"},
                                            "sub_dir": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            },
                                            "binding_count": {"type": "number"}
                                        }
                                    }
                                },
                                "binding_count": {"type": "number"}
                            },
                            "required": ["id", "name", "type", "level", "parent_id", "sub_dir", "binding_count"]
                        }
                    },
                    "binding_count": {"type": "number"}
                },
                "required": ["id", "name", "type", "level", "parent_id", "sub_dir", "binding_count"]
            }
        }
    }
}

def validate_response(response_json):
    """校验返回的JSON数据是否符合预定义的Schema"""
    try:
        validate(instance=response_json, schema=response_schema)
        print("Response JSON format is valid.")
    except jsonschema.exceptions.ValidationError as err:
        print(f"Response JSON format is invalid: {err}")

def send_post_request(payload):
    """发送POST请求并返回响应"""
    response = requests.post(BASE_URL + ENDPOINT, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print(f"Request successful, status code: {response.status_code}")
        return response.json()
    else:
        print(f"Request failed, status code: {response.status_code}")
        return None

def send_get_request(params):
    """发送GET请求并返回响应"""
    response = requests.get(BASE_URL + ENDPOINT, headers=headers, params=params)
    if response.status_code == 200:
        print(f"Request successful, status code: {response.status_code}")
        return response.json()
    else:
        print(f"Request failed, status code: {response.status_code}")
        return None

def test_api():
    """测试API并校验返回数据格式"""
    # 测试非根目录请求
    # print("\nTesting non-root directory creation...")
    # response_json = send_post_request(non_root_directory_payload)
    # if response_json:
    #     validate_response(response_json)

    # 测试获取目录树请求
    print("\nTesting get directory tree...")
    params = {"type": "app"}
    response_json = send_get_request(params)
    if response_json:
        validate_response(response_json, get_tree_response_schema)

if __name__ == "__main__":
    test_api()