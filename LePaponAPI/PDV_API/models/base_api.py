import requests
from typing import Any, Dict, Optional, Union, List
from utils.logger import get_logger

DEFAULT_TIMEOUT = 8  # segundos

class BaseAPI:
    """Classe base para simplificar clients REST.

    Fornece operações CRUD padronizadas com tratamento básico de erros.
    """
    def __init__(self, base_url: str, resource: str, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip('/')
        self.resource = resource.strip('/')
        self.timeout = timeout
        self.logger = get_logger(f"api.{self.resource}")

    def _url(self, suffix: str = "") -> str:
        return f"{self.base_url}/api/{self.resource}{suffix}"  # /api/<resource>[/suffix]

    def _request(self, method: str, url: str, **kwargs) -> Union[Dict[str, Any], List, Any, None]:
        self.logger.debug(f"request", extra={"method": method, "url": url})
        try:
            resp = requests.request(method, url, timeout=self.timeout, **kwargs)
            ok = resp.status_code < 400
            self.logger.info(
                "response",
                extra={
                    "method": method,
                    "url": url,
                    "status": resp.status_code,
                    "ok": ok
                }
            )
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return resp.text
        except requests.RequestException as e:
            self.logger.error("request_error", extra={"method": method, "url": url, "error": str(e)})
            return None

    # Métodos CRUD genéricos
    def get_all(self):
        return self._request("GET", self._url())

    def get_by_id(self, _id):
        return self._request("GET", self._url(f"/{_id}"))

    def create(self, data: Dict[str, Any]):
        return self._request("POST", self._url(), json=data)

    def update(self, _id, data: Dict[str, Any]):
        return self._request("PUT", self._url(f"/{_id}"), json=data)

    def delete(self, _id):
        return self._request("DELETE", self._url(f"/{_id}"))
