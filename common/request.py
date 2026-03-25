import requests

from common.observability import log_http_interaction

class Request:

    @staticmethod
    def _request(method, url, json=None, headers=None):
        kwargs = {"json": json, "headers": headers}
        response = requests.request(method=method, url=url, json=json, headers=headers)
        log_http_interaction(method.upper(), url, kwargs=kwargs, response=response, source="request")
        return response

    @staticmethod
    def post(url, json=None, headers=None):
        return Request._request("post", url, json=json, headers=headers)

    @staticmethod
    def get(url, headers=None):
        return Request._request("get", url, headers=headers)

    @staticmethod
    def put(url, json=None, headers=None):
        return Request._request("put", url, json=json, headers=headers)

    @staticmethod
    def delete(url, headers=None):
        return Request._request("delete", url, headers=headers)
