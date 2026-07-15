# aure-ex

SDK oficial da API AureEX para Python.

## Instalação

```bash
pip install aure-ex
```

## Uso

```python
from aure_ex import AureEx

aure_ex = AureEx(
    api_key="...",
    api_secret="...",
)

aure_ex.deposits.create({
    "method": "usdt",
    "reference": "order-1",
    "amount": 10000,
})
aure_ex.webhooks.list()
aure_ex.company.balance()
aure_ex.conversions.quote({"from": "USDT", "to": "BRL", "amount": 100})
```

## Mapa de métodos

| SDK | HTTP |
| --- | --- |
| `aure_ex.deposits` | `/v1/deposits` |
| `aure_ex.withdrawals` | `/v1/withdrawals` |
| `aure_ex.webhooks` | `/v1/webhooks` |
| `aure_ex.company.get` / `balance` | `/v1/company`, `/v1/company/balance` |
| `aure_ex.conversions` / `quote` | `/v1/conversions`, `/v1/conversions/quote` |

Docs: https://api.aure-ex.com/docs/sdks  
OpenAPI: https://api.aure-ex.com/openapi.yaml
