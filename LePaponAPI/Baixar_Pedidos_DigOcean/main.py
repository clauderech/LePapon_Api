

"""Cliente simples para escutar eventos do WebSocket do LePapon.

Observação: o servidor pode exigir autenticação via token.
Este arquivo tenta obter a URL de conexão via endpoint remoto e faz fallback
para variáveis de ambiente.
"""

import asyncio
import json
import os
from urllib.parse import parse_qs, urlparse, urlunparse

import requests
import websockets

def _mask_token(token: str) -> str:
    if not token:
        return "(vazio)"
    if len(token) <= 8:
        return "***"
    return f"{token[:4]}...{token[-4:]}"


def _http_to_ws(url: str) -> str:
    if url.startswith("https://"):
        return "wss://" + url[len("https://") :]
    if url.startswith("http://"):
        return "ws://" + url[len("http://") :]
    return url


def _normalize_public_ws_uri(uri: str) -> str:
    """Normaliza URIs retornadas pelo servidor (ex: ws://localhost:3001) para uso externo."""
    try:
        parsed = urlparse(uri)
        host = parsed.hostname
        if host in {"localhost", "127.0.0.1"}:
            port = parsed.port or 3001
            fixed = parsed._replace(netloc=f"lepapon.com.br:{port}")
            return urlunparse(fixed)
    except Exception:
        pass
    return uri


# Obter informações de conexão dinamicamente
def get_connection_info() -> dict:
    endpoint = os.getenv("WS_CONNECTION_INFO_ENDPOINT", "https://lepapon.com.br/api/websocket/connection")

    # 1) Tenta buscar a URL pronta (ideal: já vem com token)
    try:
        response = requests.get(endpoint, timeout=10)
        if response.status_code == 200:
            payload = response.json() or {}
            ws = ((payload.get("data") or {}).get("websocket") or {})

            raw_url = ws.get("url")
            port = ws.get("port")

            if raw_url:
                ready = _normalize_public_ws_uri(_http_to_ws(raw_url))
                return {"uri": ready}

            # Compat: se o endpoint só informar porta
            if port:
                return {"uri": f"ws://lepapon.com.br:{port}"}

    except Exception:
        # Silencioso e segue para fallback abaixo
        pass

    # 2) Fallback para env vars
    ws_url = os.getenv("WS_URL", "ws://lepapon.com.br:3001")
    token = os.getenv("WS_AUTH_TOKEN") or os.getenv("WEBSOCKET_TOKEN")
    return {"uri": ws_url, "token": token}


def get_ws_token() -> str | None:
    token_endpoint = os.getenv("WS_TOKEN_ENDPOINT", "https://lepapon.com.br/api/websocket/token")
    try:
        r = requests.get(token_endpoint, timeout=10)
        if r.status_code != 200:
            return None
        payload = r.json() or {}
        token = payload.get("token")
        return token if isinstance(token, str) and token else None
    except Exception:
        return None


def _ensure_token_in_uri(uri: str, token: str | None) -> str:
    parsed = urlparse(uri)
    qs = parse_qs(parsed.query)
    if "token" in qs:
        return uri
    if not token:
        return uri
    joiner = "&" if parsed.query else "?"
    return f"{uri}{joiner}token={token}"

async def listen_websocket():
    info = get_connection_info()
    uri = info.get("uri")
    token = info.get("token")

    if not isinstance(uri, str) or not uri:
        raise ValueError("WS connection URI ausente ou inválida (chave 'uri').")

    uri = _normalize_public_ws_uri(uri)

    # Se não veio token por env/connection-info, tenta obter via endpoint HTTPS.
    if not token:
        token = get_ws_token()

    uri = _ensure_token_in_uri(uri, token)

    if "token=" not in uri:
        raise RuntimeError(
            "Token do WebSocket ausente. Configure WS_AUTH_TOKEN/WEBSOCKET_TOKEN "
            "ou verifique WS_TOKEN_ENDPOINT (/api/websocket/token)."
        )

    # Evita vazar token no console
    safe_uri: str = uri
    if "token=" in safe_uri:
        safe_uri = safe_uri.split("token=")[0] + "token=" + _mask_token((safe_uri.split("token=")[1]).split("&")[0])
    print(f"🔌 Conectando ao WebSocket: {safe_uri}")

    async with websockets.connect(uri) as websocket:
        print("✅ Conectado ao WebSocket LePapon!")
        print("👂 Aguardando eventos...\n")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                event_type = data.get('event', 'unknown')
                payload = data.get('data') or {}
                novo = payload.get('novo') if isinstance(payload, dict) else None
                if not isinstance(novo, dict):
                    novo = payload if isinstance(payload, dict) else {}
                
                print(f"\n📨 Evento recebido: {event_type}")
                print(f"📋 Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Processa diferentes tipos de eventos
                if event_type == 'new_order':
                    order_id = novo.get('orderId')
                    pedidos_ids = novo.get('pedidosIds')
                    if not order_id and isinstance(pedidos_ids, list) and pedidos_ids:
                        order_id = pedidos_ids[0]

                    total = novo.get('totalValue')
                    if total is None:
                        total = novo.get('valorTotal')

                    items = novo.get('items')
                    if items is None:
                        items = novo.get('itensPedido')
                    if not isinstance(items, list):
                        items = []

                    print(f"\n🍔 NOVO PEDIDO: {order_id}")
                    if isinstance(total, (int, float)):
                        print(f"💰 Valor Total: R$ {total:.2f}")
                    else:
                        print(f"💰 Valor Total: {total}")
                    print(f"📦 Itens: {len(items)}")
                    
                elif event_type == 'new_message':
                    print(f"\n💬 Nova mensagem de: {novo.get('sender')}")
                    print(f"📝 Texto: {novo.get('text')}")
                    
                elif event_type == 'gemini_reply':
                    print(f"\n🤖 Resposta do Gemini para: {novo.get('contactName')}")
                    print(f"💭 Texto: {novo.get('text')}")
                
                print("-" * 50)
                
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Conexão fechada")
        except Exception as e:
            print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    print("🚀 Cliente WebSocket LePapon iniciado")
    print("=" * 50)
    asyncio.run(listen_websocket())