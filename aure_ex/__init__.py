"""SDK oficial da API AureEX para Python (crypto only)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

__version__ = "0.1.0"


class AureExError(Exception):
    """Erro tipado da API (envelope `success: false` ou falha HTTP)."""
    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: Any = None,
        status_code: int = 0,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details
        self.status_code = status_code


class _HttpClient:
    """Cliente HTTP autenticado com retry em 429."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.aure-ex.com/v1",
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        """Executa requisição autenticada e desempacota o envelope `data`."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        attempt = 0

        while True:
            attempt += 1
            headers = {
                "X-Api-Key": self.api_key,
                "X-Api-Secret": self.api_secret,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            if extra_headers:
                headers.update(extra_headers)

            data = None if body is None else json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

            try:
                with urllib.request.urlopen(req) as response:
                    raw = response.read().decode("utf-8")
                    status = response.status
                    retry_after = response.headers.get("Retry-After", "1")
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8")
                status = exc.code
                retry_after = exc.headers.get("Retry-After", "1") if exc.headers else "1"

            if status == 429 and attempt <= self.max_retries + 1:
                time.sleep(max(1, int(retry_after or "1")))
                continue

            decoded = json.loads(raw) if raw else None

            if status >= 400:
                error = (decoded or {}).get("error") if isinstance(decoded, dict) else None
                message = (
                    error.get("message")
                    if isinstance(error, dict)
                    else "Request failed."
                )
                raise AureExError(
                    str(message),
                    error.get("code") if isinstance(error, dict) else None,
                    error.get("details") if isinstance(error, dict) else None,
                    status,
                )

            if isinstance(decoded, dict) and "data" in decoded:
                return decoded["data"]

            return decoded


class _CrudResource:
    """Recurso CRUD genérico (list/create/get/update/delete)."""

    def __init__(self, http: _HttpClient, base_path: str) -> None:
        self._http = http
        self._base_path = base_path

    def list(self, **query: Any) -> Any:
        path = self._base_path
        if query:
            path = f"{path}?{urllib.parse.urlencode(query)}"
        return self._http.request("GET", path)

    def create(self, payload: dict[str, Any], idempotency_key: str | None = None) -> Any:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._http.request("POST", self._base_path, payload, headers)

    def get(self, id: str) -> Any:
        return self._http.request("GET", f"{self._base_path}/{urllib.parse.quote(id)}")

    def update(self, id: str, payload: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"{self._base_path}/{urllib.parse.quote(id)}", payload)

    def delete(self, id: str) -> Any:
        return self._http.request("DELETE", f"{self._base_path}/{urllib.parse.quote(id)}")


class _Company:
    """Empresa autenticada e saldo."""

    def __init__(self, http: _HttpClient) -> None:
        self._http = http

    def get(self) -> Any:
        """Dados da empresa (GET /company)."""
        return self._http.request("GET", "/company")

    def balance(self) -> Any:
        """Saldo disponível (GET /company/balance)."""
        return self._http.request("GET", "/company/balance")


class _Conversions(_CrudResource):
    """Conversões crypto (ex.: USDT/BRL)."""

    def __init__(self, http: _HttpClient) -> None:
        super().__init__(http, "/conversions")

    def quote(self, payload: dict[str, Any]) -> Any:
        """Cotação de conversão (POST /conversions/quote)."""
        return self._http.request("POST", "/conversions/quote", payload)


class AureEx:
    """Facade principal da API AureEX (crypto only)."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.aure-ex.com/v1",
        max_retries: int = 2,
    ) -> None:
        api_key = (api_key or "").strip()
        api_secret = (api_secret or "").strip()
        if not api_key or not api_secret:
            raise AureExError("api_key and api_secret are required.")
        self._http = _HttpClient(api_key, api_secret, base_url, max_retries)
        self.deposits = _CrudResource(self._http, "/deposits")
        self.withdrawals = _CrudResource(self._http, "/withdrawals")
        self.webhooks = _CrudResource(self._http, "/webhooks")
        self.company = _Company(self._http)
        self.conversions = _Conversions(self._http)


# Tipos gerados a partir do OpenAPI público (quando presentes).
try:
    from aure_ex import generated as generated
except ImportError:  # pragma: no cover
    generated = None  # type: ignore[assignment]


__all__ = [
    "AureEx",
    "AureExError",
    "generated",
]
