import requests


class DdApi:
    def __init__(self, api_host, api_key, app_key):
        self.api_host = api_host
        self.api_key = api_key
        self.app_key = app_key

    def request(self, path):
        url = f"{self.api_host}{path}"
        req = requests.get(
            url,
            headers={
                "DD-API-KEY": self.api_key,
                "DD-APPLICATION-KEY": self.app_key,
                "Content-Type": "application/json",
            },
        )
        req.raise_for_status()
        return req.json()

    @classmethod
    def from_config(cls, config):
        return cls(
            api_host=config["datadog_url"],
            api_key=config["api_key"],
            app_key=config["app_key"],
        )
