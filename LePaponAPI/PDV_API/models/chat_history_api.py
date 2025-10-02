import requests

class ChatHistoryAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def get_history(self):
        resp = requests.get(f"{self.base_url}/chat-history")
        resp.raise_for_status()
        return resp.json()

    def get_history_by_session(self):
        resp = requests.get(f"{self.base_url}/chat-history?group_by=session_id")
        resp.raise_for_status()
        return resp.json()

    def send_message(self, sender, text, session_id=None):
        resp = requests.post(
            f"{self.base_url}/chat-history",
            json={"sender": sender, "text": text, "session_id": session_id}
        )
        resp.raise_for_status()
        return resp.json()

    def delete_history(self):
        resp = requests.delete(f"{self.base_url}/chat-history")
        resp.raise_for_status()
        return resp.json()
