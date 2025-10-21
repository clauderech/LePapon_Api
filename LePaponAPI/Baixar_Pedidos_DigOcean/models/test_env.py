#!/usr/bin/env python3
"""
Script para testar carregamento de variáveis de ambiente
"""
import os
from dotenv import load_dotenv

print("=" * 80)
print("🧪 TESTE DE VARIÁVEIS DE AMBIENTE")
print("=" * 80)

# Mostra o diretório atual
print(f"\n📁 Diretório atual: {os.getcwd()}")

# Tenta carregar o .env
env_paths = [
    ".env",
    "../.env",
    "../../.env",
    "../../../.env",
    "../../../../.env",
    "/home/claus/Projetos/Python/LePapon_Api/.env"
]

print(f"\n🔍 Procurando arquivo .env...\n")
for path in env_paths:
    abs_path = os.path.abspath(path)
    exists = os.path.exists(abs_path)
    print(f"   {'✅' if exists else '❌'} {abs_path}")
    if exists:
        print(f"      👉 Usando este arquivo!\n")
        load_dotenv(dotenv_path=abs_path)
        break

# Mostra as variáveis carregadas
print("=" * 80)
print("📋 VARIÁVEIS CARREGADAS:")
print("=" * 80)

env_vars = {
    'WS_HOST': os.getenv('WS_HOST', 'NÃO DEFINIDO'),
    'WS_PORT': os.getenv('WS_PORT', 'NÃO DEFINIDO'),
    'WS_AUTH_TOKEN': os.getenv('WS_AUTH_TOKEN', 'NÃO DEFINIDO'),
    'API_BASE_URL': os.getenv('API_BASE_URL', 'NÃO DEFINIDO'),
    'API_KEY': os.getenv('API_KEY', 'NÃO DEFINIDO'),
}

for key, value in env_vars.items():
    if value != 'NÃO DEFINIDO' and len(value) > 20:
        display_value = f"{value[:15]}..."
    else:
        display_value = value
    print(f"   {key}: {display_value}")

print("=" * 80)

# URI final do WebSocket
ws_host = os.getenv('WS_HOST', 'lepapon.com.br')
ws_port = os.getenv('WS_PORT', '3001')
ws_token = os.getenv('WS_AUTH_TOKEN', 'lepapon-secret')
ws_uri = f"ws://{ws_host}:{ws_port}?token={ws_token}"

print(f"\n🌐 URI do WebSocket: {ws_uri}")
print("=" * 80)
