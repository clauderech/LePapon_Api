

# client_lepapon.py
import asyncio
import websockets
import json
import requests

# Obter informações de conexão dinamicamente
def get_connection_info():
    try:
        response = requests.get('https://lepapon.com.br:3001/api/websocket/connection')
        if response.status_code == 200:
            data = response.json()
            return {
                'url': f"ws://lepapon.com.br:{data['data']['websocket']['port']}",
                'token': data['data']['websocket']['url'].split('token=')[1] if 'token=' in data['data']['websocket']['url'] else 'lepapon-secret'
            }
    except:
        pass
    
    # Fallback para valores padrão
    return {'url': 'ws://lepapon.com.br:3001', 'token': 'lepapon-secret'}

async def listen_websocket():
    info = get_connection_info()
    uri = f"{info['url']}?token={info['token']}"
    
    print(f"🔌 Conectando ao WebSocket: {uri}")
    
    async with websockets.connect(uri) as websocket:
        print("✅ Conectado ao WebSocket LePapon!")
        print("👂 Aguardando eventos...\n")
        
        try:
            async for message in websocket:
                data = json.loads(message)
                event_type = data.get('event', 'unknown')
                
                print(f"\n📨 Evento recebido: {event_type}")
                print(f"📋 Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Processa diferentes tipos de eventos
                if event_type == 'new_order':
                    order_data = data.get('data', {})
                    print(f"\n🍔 NOVO PEDIDO: {order_data.get('orderId')}")
                    print(f"💰 Valor Total: R$ {order_data.get('totalValue'):.2f}")
                    print(f"📦 Itens: {len(order_data.get('items', []))}")
                    
                elif event_type == 'new_message':
                    msg_data = data.get('data', {})
                    print(f"\n💬 Nova mensagem de: {msg_data.get('sender')}")
                    print(f"📝 Texto: {msg_data.get('text')}")
                    
                elif event_type == 'gemini_reply':
                    print(f"\n🤖 Resposta do Gemini para: {data.get('contactName')}")
                    print(f"💭 Texto: {data.get('text')}")
                
                print("-" * 50)
                
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Conexão fechada")
        except Exception as e:
            print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    print("🚀 Cliente WebSocket LePapon iniciado")
    print("=" * 50)
    asyncio.run(listen_websocket())