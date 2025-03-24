import json

import requests

from configs import dify_config


class OpendsClient:
    def __init__(self):
        self.base_url = dify_config.OPENDS_URL
        self.access_token = dify_config.OPENDS_ACCESS_TOKEN

    def _send_request(self, method, endpoint, json=None, params=None):

        url = f"{self.base_url}{endpoint}?access_token={self.access_token}"
        response = requests.request(
            method, url, json=json, params=params
        )

        return response.json()

    def dmc_folder_tree(self):
        response = self._send_request("POST", "/api/dmc/folder/tree")
        return response["result"]

    def dmc_tb_info(self, tb_id):
        params = {"tb_id": tb_id}
        response = self._send_request("POST", "/api/dmc/tb/info", json=None, params=params)
        return response["result"]

    def get_etl_tree_with_tblist(self):
        response = self._send_request("POST", "/api/etl/folder/get_etl_tree_with_tblist")
        return response["result"]

    def etl_list_only_tb(self, filter_tree, folder_id):
        params = {"filter_tree": filter_tree, "folder_id": folder_id}
        response = self._send_request("POST", "/api/etl/folder/etl_list_only_tb", params=params)
        return response["result"]

    def etl_filter(self, filter_str):
        params = {"filter_str": filter_str}
        response = self._send_request("POST", "/api/etl/folder/etl_filter", params=params)
        return response["result"]

    def etl_tb_info(self, tb_id):
        params = {"tb_id": tb_id}
        response = self._send_request("POST", "/api/etl/tb/info", json=None, params=params)
        return response["result"]

    def etl_tb_list(self, search_key):
        params = {"search_key": search_key}
        response = self._send_request("POST", "/api/etl/folder/etl_tb_list", json=None, params=params)
        return response["result"]

    def tb_data_query(self, tb_id, fields, limit):
        params = {"tb_id": tb_id, "fields": json.dumps(fields), "limit": limit}
        response = self._send_request("POST", "/api/tb/query", json=None, params=params)
        return response["result"]

    def ds_list(self):
        response = self._send_request("POST", "/api/ds/list", json=None, params=None)
        return response["result"]

    def ds_create(self, name):
        params = {"name": name}
        response = self._send_request("POST", "/api/ds/create", json=None, params=params)
        return response["result"]

    def tb_create(self, name, ds_id, schema, title, remark):
        data = {"name": name, "ds_id": ds_id, "schema": schema, "title": title, "remark": remark, "dereplication": 0}
        response = self._send_request("POST", "/api/tb/create", json=data, params=None)
        return response["result"]

    def etl_tb_create(self, name, schema, title, remark):
        data = {"name": name, "schema": schema, "title": title, "remark": remark, "dereplication": 0}
        response = self._send_request("POST", "/api/etl/tb/create", json=data, params=None)
        return response["result"]

    def tb_data_insert(self, tb_id, fields, data):
        params = {"tb_id": tb_id, "fields": json.dumps(fields)}
        response = self._send_request("POST", "/api/data/insert", json=data, params=params)
        return response["result"]

    def tb_commit(self, tb_id):
        params = {"tb_id": tb_id}
        response = self._send_request("POST", "/api/tb/commit", json=None, params=params)
        return response["result"]

    def tb_update(self, tb_ids):
        params = {"tb_ids": json.dumps(tb_ids)}
        response = self._send_request("POST", "/api/tb/update", json=None, params=params)
        return response["result"]
