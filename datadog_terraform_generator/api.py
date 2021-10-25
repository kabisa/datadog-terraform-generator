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
    def from_args(cls, args):
        return cls(api_host=args.api_host, api_key=args.api_key, app_key=args.app_key)
