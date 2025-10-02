import requests

class SessionAgentAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def takeOver(self, data):
        return requests.post(f"{self.base_url}/session/takeover", json=data).json()

    def release(self, data):
        return requests.post(f"{self.base_url}/session/release", json=data).json()
