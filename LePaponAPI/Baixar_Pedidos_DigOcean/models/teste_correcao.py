#!/usr/bin/env python3
"""
Teste da correção de validação de tipos
"""

import json
import sys
import os

# Adiciona o diretório atual ao path para importar o módulo
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from registra_pedido import processar_json

def testar_correcao():
    """Testa a correção com os dados que causaram erro"""
    
    # Dados do exemplo que causou erro
    dados_teste = [
        {
            "id_pedidos": 141, 
            "nome": "Claudemir", 
            "fone": "555496860055", 
            "id_Prod": 10101, 
            "qtd": "1",  # String que deve ser convertida para float
            "data": "2025-10-27T03:00:00.000Z", 
            "hora": "16:32:32", 
            "observ": "Completo"
        }, 
        {
            "id_pedidos": 142, 
            "nome": "Claudemir", 
            "fone": "555496860055", 
            "id_Prod": 10103, 
            "qtd": "1",  # String que deve ser convertida para float
            "data": "2025-10-27T03:00:00.000Z", 
            "hora": "16:46:48", 
            "observ": "completo"
        }, 
        {
            "id_pedidos": 143, 
            "nome": "Claudemir", 
            "fone": "555496860055", 
            "id_Prod": 10201, 
            "qtd": "1",  # String que deve ser convertida para float
            "data": "2025-10-27T03:00:00.000Z", 
            "hora": "16:55:32", 
            "observ": "completo"
        }
    ]
    
    # Converte para JSON string
    dados_json = json.dumps(dados_teste, ensure_ascii=False)
    
    print("🧪 TESTE DE CORREÇÃO DA VALIDAÇÃO")
    print("=" * 50)
    print(f"📋 Dados de teste:")
    print(f"   - {len(dados_teste)} pedidos")
    print(f"   - Cliente: Claudemir")
    print(f"   - Telefone: 555496860055") 
    print(f"   - qtd como string: '{dados_teste[0]['qtd']}'")
    print("=" * 50)
    
    try:
        print("⏳ Processando pedidos...")
        resultado = processar_json(dados_json)
        
        if resultado and resultado.get('sucesso'):
            print("✅ SUCESSO!")
            print(f"📋 {resultado.get('mensagem')}")
            print(f"📦 Pedidos processados: {len(resultado.get('pedidos', []))}")
        else:
            print("❌ FALHA!")
            if resultado:
                print(f"📋 Erro: {resultado.get('mensagem')}")
            else:
                print("📋 Resultado nulo")
                
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_correcao()