import requests


class DdApi:
    def __init__(self, api_host, api_key, app_key):
        self.api_host = api_host
        self.api_key = api_key
        self.app_key = app_key

    def request(self, path, data=None):
        if data is None:
            req = requests.get(
                url=self.check_url(path),
                headers=self.get_headers(),
            )
        else:
            req = requests.post(
                url=self.check_url(path), headers=self.get_headers(), json=data
            )
        return self.read_response(req)

    def get_headers(self):
        return {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def check_url(self, path):
        if self.api_host.endswith("/") and path.startswith("/"):
            path = path[1:]
        url = f"{self.api_host}{path}"
        return url

    def read_response(self, req):
        if req.status_code == 429:
            print(
                "Max requests per second:",
                int(req.headers["x-ratelimit-limit"])
                / int(req.headers["x-ratelimit-period"]),
                "\nOr sleep time:",
                int(req.headers["x-ratelimit-period"])
                / int(req.headers["x-ratelimit-limit"]),
            )
        req.raise_for_status()
        data = req.json()
        if data.get("status", "") == "error":
            raise Exception(f"API quest failed: {data['error']}")
        return data

    @classmethod
    def from_config(cls, config):
        return cls(
            api_host=config["datadog_url"],
            api_key=config["api_key"],
            app_key=config["app_key"],
        )
