# __author__ "lisiyu"
# date 2025/2/23

import requests
import json
from configparser import ConfigParser

# 常量配置
config = ConfigParser()
config.read('../config.ini')
AUTH_TOKEN = config.get('API', 'authorization_token')
API_URL = "http://127.0.0.1:5001/console/api/directory"

# 请求头配置
headers = {
    "Content-Type": "application/json",
    "Authorization": AUTH_TOKEN
}

# 有效测试数据（根据req_body_other的schema构造）
valid_payload = {
    "name": "test_directory",
    "type": "app",
    "parent_id": "b22d949f-e158-4905-8c26-8090813943d7"
}

def test_create_directory():
    try:
        # 发送请求
        response = requests.post(
            url=API_URL,
            headers=headers,
            data=json.dumps(valid_payload))

        # 基础断言
        assert response.status_code == 200, f"非预期状态码: {response.status_code}"

        # 解析响应
        response_json = response.json()
        print("完整响应:", json.dumps(response_json, indent=2))

        # 响应格式验证（根据res_body的schema）
        assert "message" in response_json, "响应缺少message字段"
        assert "directory_id" in response_json, "响应缺少directory_id字段"
        assert isinstance(response_json["message"], str), "message字段类型错误"
        assert isinstance(response_json["directory_id"], str), "directory_id字段类型错误"

        print("\n测试通过 ✅")
        return True

    except Exception as e:
        print("\n测试失败 ❌ 错误信息:", str(e))
        return False


if __name__ == "__main__":
    test_result = test_create_directory()
    print("测试结果:", "成功" if test_result else "失败")