# websocket_client.py
import asyncio
import websockets
import json
from pedidosDropletModel import LePaponAPI

URL_BASE = "http://lepapon.api"

api = LePaponAPI(URL_BASE)

async def listen_custom_messages():
    uri = "ws://lepapon.com.br:3001?token=lepapon-secret"
    
    while True:
        try:
            async with websockets.connect(
                uri,
                ping_interval=20,
                ping_timeout=30
            ) as websocket:
                print("✅ Conectado ao WebSocket")
                
                async for message in websocket:
                    data = json.loads(message)
                    event = data.get('event')
                    payload = data.get('data', {})
                    
                    # Processa mensagens customizadas
                    if event == 'custom_message':
                        session_id = payload.get('session_id')
                        novo = payload.get('novo')
                        pedido = api.buscar_por_fone(session_id)
                        print(f"\npedido encontrado: {pedido}")
                        print(f"\n📨 Mensagem customizada:")
                        print(f"   Sessão: {session_id}")
                        print(f"   Dados: {novo}")
                    
                    elif event == 'session_update':
                        session_id = payload.get('session_id')
                        novo = payload.get('novo')
                        print(f"\n🔄 Atualização de sessão:")
                        print(f"   Sessão: {session_id}")
                        print(f"   Atualização: {json.dumps(novo, indent=2)}")
                    
                    elif event == 'session_notification':
                        session_id = payload.get('session_id')
                        novo = payload.get('novo')
                        print(f"\n🔔 Notificação:")
                        print(f"   Sessão: {session_id}")
                        print(f"   Conteúdo: {json.dumps(novo, indent=2)}")

        except websockets.exceptions.ConnectionClosed as e:
            print(f"🔌 Conexão WebSocket fechada: {e}. Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"❌ Ocorreu um erro: {e}. Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)

asyncio.run(listen_custom_messages())