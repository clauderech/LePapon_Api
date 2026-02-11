# Prompt — Agente para criar conexão WebSocket (LePapon)

Você é um agente de IA atuando como engenheiro Python sênior dentro deste repositório. Sua missão é criar um **cliente WebSocket robusto** para consumir eventos do LePapon.

## Contexto do servidor
- A API HTTP pública roda em **HTTPS**: `https://lepapon.com.br`.
- O WebSocket público roda na porta **3001** (sem TLS): `ws://lepapon.com.br:3001`.
- O servidor exige autenticação (`auth_required: true`).
- O token deve ser obtido via endpoint HTTPS:
  - `GET https://lepapon.com.br/api/websocket/token` → retorna JSON com `token`.
- Um endpoint informativo existe:
  - `GET https://lepapon.com.br/api/websocket/connection` → pode retornar URLs como `ws://localhost:3001` (não usar “localhost” no cliente remoto).

## Objetivo
Implementar um módulo de conexão WebSocket que:
1. Obtém o token automaticamente (ou por env var).
2. Conecta em `ws://lepapon.com.br:3001?token=<TOKEN>`.
3. Mantém conexão com **reconexão automática**.
4. Processa eventos recebidos (no mínimo `new_order`, `new_message`, `gemini_reply`, `message_status`).
5. Não vaza o token em logs/prints.

## Regras e restrições
- Linguagem: Python 3.12.
- Use a lib `websockets` e `asyncio`.
- **Não hardcode tokens** no código final.
- Token deve vir de:
  1) env var (`WS_AUTH_TOKEN` ou `WEBSOCKET_TOKEN`) **ou**
  2) `GET https://lepapon.com.br/api/websocket/token`.
- Se o endpoint de connection-info retornar `ws://localhost:3001`, normalize para `ws://lepapon.com.br:3001`.
- Nunca imprimir o token completo; ao logar a URL, mascarar (ex: `cca4...0a51`).

## Onde implementar
Crie/edite arquivos **dentro deste módulo**:
- `LePaponAPI/Baixar_Pedidos_DigOcean/utils/websocket_client.py` (novo)

Opcional (se fizer sentido):
- integrar com `LePaponAPI/Baixar_Pedidos_DigOcean/main.py` para usar o novo módulo.

## Interface desejada
No arquivo `websocket_client.py`, implementar algo semelhante a:

- `class LePaponWebSocketClient:`
  - `__init__(self, ws_url: str = ..., token_endpoint: str = ..., ping_interval: int = 20, ping_timeout: int = 30, reconnect_delay: int = 5)`
  - `async def run_forever(self) -> None` (loop com reconexão)
  - `async def handle_message(self, message: str) -> None` (parse JSON + dispatch)

Também crie helpers:
- `def get_ws_token(...) -> str | None`
- `def ensure_token_in_uri(uri: str, token: str | None) -> str`
- `def normalize_public_ws_uri(uri: str) -> str`
- `def mask_token(token: str) -> str`

## Formato dos eventos
O servidor envia mensagens JSON. Na prática, muitos payloads chegam assim:

```json
{
  "event": "new_order",
  "data": {
    "session_id": "555...",
    "novo": {
      "pedidosIds": [789],
      "valorTotal": 22,
      "itensPedido": [{"id": 10101, "Qtde": 1}]
    }
  }
}
```

Regras de parsing:
- Ler `event = data.get("event", "unknown")`.
- O payload útil geralmente está em `data["data"]["novo"]`.
- Tratar campos alternativos:
  - total: `totalValue` ou `valorTotal`
  - itens: `items` ou `itensPedido`
  - orderId: `orderId` ou primeiro elemento de `pedidosIds`
- O código não pode quebrar se algum campo vier ausente ou `None`.

## Observabilidade
- Adote `logging` (não apenas `print`).
- Logar:
  - conexão estabelecida
  - reconexões (com contador)
  - eventos recebidos (tipo)
  - erros de parse JSON e exceções

## Critérios de aceite
- Rodar localmente com:
  - `python LePaponAPI/Baixar_Pedidos_DigOcean/main.py` (se integrar) **ou**
  - um `if __name__ == "__main__":` no próprio `websocket_client.py`.
- Deve conectar e receber eventos sem erro 401 (obtendo token automaticamente).
- Não deve tentar conectar em `ws://localhost:3001`.
- Não deve crashar ao receber `new_order` com `valorTotal` e `itensPedido`.

## Variáveis de ambiente suportadas
- `WS_URL` (default: `ws://lepapon.com.br:3001`)
- `WS_AUTH_TOKEN` ou `WEBSOCKET_TOKEN` (opcional)
- `WS_TOKEN_ENDPOINT` (default: `https://lepapon.com.br/api/websocket/token`)
- `WS_CONNECTION_INFO_ENDPOINT` (default: `https://lepapon.com.br/api/websocket/connection`)

## Entrega
Ao finalizar:
1. Garanta que o código está limpo e executável.
2. Informe como executar e como configurar env vars.
3. Se adicionar dependências, atualizar `requirements.txt` do módulo.
