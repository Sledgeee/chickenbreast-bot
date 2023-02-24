import requests


def api_request(method, path, json=None, params=None):
    try:
        api_endpoint = "https://chickenapi-1-r8060741.deta.app"
        response = requests.request(
            method=method,
            url=f'{api_endpoint}/{path}/',
            params=params,
            json=json
        )
        return response.json()
    except:
        pass
