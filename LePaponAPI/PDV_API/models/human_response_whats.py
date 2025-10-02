import requests

class HumanResponseWhatsSender:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def send_response(self, data, headers=None):
        """
        Envia uma mensagem para o endpoint /send-human-response.

        :param data: dict com os dados a serem enviados no corpo do JSON.
        :param headers: dict opcional com headers HTTP.
        :return: requests.Response
        """
        url = f"{self.base_url}/send-human-response"
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)
        response = requests.post(url, json=data, headers=default_headers)
        response.raise_for_status()
        return response

# Exemplo de uso:
# sender = HumanResponseWhatsSender("http://localhost:8000")
# response = sender.send_response({"message": "Olá, mundo!", "user_id": 123})
# print(response.json())