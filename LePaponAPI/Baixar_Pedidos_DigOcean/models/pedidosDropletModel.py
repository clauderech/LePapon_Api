# listar_pedidos.py
"""
Script para listar pedidos da API LePapon
Autor: Sistema LePapon
Data: 15/10/2025

Funcionalidades:
- Listar todos os pedidos
- Buscar pedido por ID
- Filtrar pedidos por data, cliente ou produto
- Exportar para CSV/JSON
- Estatísticas de pedidos
"""

import requests
import json
import os
from typing import Optional, List, Dict
import csv
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

MINNHA_API_KEY = os.getenv('MINHA_API_KEY')

class LePaponAPI:
    """Cliente para a API de Pedidos do LePapon"""
    
    def __init__(self, base_url: str = "", api_key: str = ""):
        """
        Inicializa o cliente da API
        
        Args:
            base_url: URL base da API (padrão: http://localhost:3000)
            api_key: Chave de API (busca de .env se não fornecida)
        """
        self.base_url = base_url or os.getenv('API_REMOTE_BASE_URL', 'https://lepapon.com.br')
        self.api_key = api_key or os.getenv('MINHA_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ API Key não encontrada! Configure MINHA_API_KEY no arquivo .env")
        
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def listar_pedidos(self) -> List[Dict]:
        """
        Lista todos os pedidos
        
        Returns:
            Lista de pedidos
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/pedidos",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao listar pedidos: {e}")
            return []
    
    def buscar_pedido(self, pedido_id: int) -> Optional[Dict]:
        """
        Busca um pedido específico por ID
        
        Args:
            pedido_id: ID do pedido
            
        Returns:
            Dados do pedido ou None se não encontrado
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/pedidos/{pedido_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 404:
                print(f"⚠️  Pedido #{pedido_id} não encontrado")
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao buscar pedido: {e}")
            return None
    
    def criar_pedido(self, dados: Dict) -> Optional[Dict]:
        """
        Cria um novo pedido
        
        Args:
            dados: Dados do pedido (idOrdemPedidos, idItem, Qtde, Observ)
            
        Returns:
            Pedido criado ou None se erro
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pedidos",
                headers=self.headers,
                json=dados,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao criar pedido: {e}")
            return None

    def buscar_por_fone(self, fone: str) -> List[Dict]:
        """
        Busca pedidos por número de telefone na API.
        
        Args:
            fone: Número de telefone para buscar.
            
        Returns:
            Lista de pedidos encontrados ou lista vazia.
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/pedidos/fone/{fone}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao buscar pedidos por fone: {e}")
            return []


class PedidosManager:
    """Gerenciador de pedidos com funcionalidades avançadas"""
    
    def __init__(self, api: LePaponAPI):
        self.api = api
    
    def exibir_pedidos(self, pedidos: List[Dict], detalhado: bool = False):
        """
        Exibe pedidos formatados no console
        
        Args:
            pedidos: Lista de pedidos
            detalhado: Se True, exibe todos os campos
        """
        if not pedidos:
            print("\n📭 Nenhum pedido encontrado")
            return
        
        print(f"\n📦 Total de pedidos: {len(pedidos)}")
        print("=" * 80)
        
        for idx, pedido in enumerate(pedidos, 1):
            print(f"\n{idx}. Pedido ID: {pedido.get('id', 'N/A')}")
            print(f"   👤 Cliente: {pedido.get('nome', 'N/A')}")
            print(f"   📱 Telefone: {pedido.get('fone', 'N/A')}")
            print(f"   🍔 Produto ID: {pedido.get('id_Prod', 'N/A')}")
            print(f"   📊 Quantidade: {pedido.get('qtd', 'N/A')}")
            print(f"   📅 Data: {pedido.get('data', 'N/A')}")
            print(f"   🕐 Hora: {pedido.get('hora', 'N/A')}")
            print(f"   📝 Observação: {pedido.get('observ', 'N/A')}")
            
            if detalhado:
                print(f"   📋 Dados completos: {json.dumps(pedido, indent=6, ensure_ascii=False)}")
            
            print("-" * 80)
    
    def filtrar_por_cliente(self, pedidos: List[Dict], nome_cliente: str) -> List[Dict]:
        """Filtra pedidos por nome do cliente"""
        return [
            p for p in pedidos 
            if nome_cliente.lower() in str(p.get('nome', '')).lower()
        ]
    
    def filtrar_por_data(self, pedidos: List[Dict], data: str) -> List[Dict]:
        """Filtra pedidos por data (formato: YYYY-MM-DD)"""
        return [
            p for p in pedidos 
            if str(p.get('data', '')) == data
        ]
    
    def filtrar_por_telefone(self, pedidos: List[Dict], telefone: str) -> List[Dict]:
        """Filtra pedidos por telefone"""
        return [
            p for p in pedidos 
            if telefone in str(p.get('fone', ''))
        ]
    
    def estatisticas(self, pedidos: List[Dict]):
        """Exibe estatísticas dos pedidos"""
        if not pedidos:
            print("\n📊 Sem dados para estatísticas")
            return
        
        total_pedidos = len(pedidos)
        clientes_unicos = len(set(p.get('nome') for p in pedidos if p.get('nome')))
        produtos_unicos = len(set(p.get('id_Prod') for p in pedidos if p.get('id_Prod')))
        
        # Quantidade total
        qtd_total = sum(float(p.get('qtd', 0)) for p in pedidos)
        
        # Pedidos por data
        pedidos_por_data = {}
        for p in pedidos:
            data = p.get('data', 'Sem data')
            pedidos_por_data[data] = pedidos_por_data.get(data, 0) + 1
        
        print("\n📊 ESTATÍSTICAS DE PEDIDOS")
        print("=" * 80)
        print(f"📦 Total de pedidos: {total_pedidos}")
        print(f"👥 Clientes únicos: {clientes_unicos}")
        print(f"🍔 Produtos únicos: {produtos_unicos}")
        print(f"📊 Quantidade total: {qtd_total}")
        
        print(f"\n📅 Pedidos por data:")
        for data, qtd in sorted(pedidos_por_data.items(), reverse=True)[:5]:
            print(f"   {data}: {qtd} pedidos")
        
        print("=" * 80)
    
    def exportar_csv(self, pedidos: List[Dict], filename: str = 'pedidos.csv'):
        """Exporta pedidos para CSV"""
        if not pedidos:
            print("❌ Sem pedidos para exportar")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'nome', 'fone', 'id_Prod', 'qtd', 'data', 'hora', 'observ']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for pedido in pedidos:
                    writer.writerow({
                        'id': pedido.get('id', ''),
                        'nome': pedido.get('nome', ''),
                        'fone': pedido.get('fone', ''),
                        'id_Prod': pedido.get('id_Prod', ''),
                        'qtd': pedido.get('qtd', ''),
                        'data': pedido.get('data', ''),
                        'hora': pedido.get('hora', ''),
                        'observ': pedido.get('observ', '')
                    })
            
            print(f"✅ Pedidos exportados para: {filename}")
        except Exception as e:
            print(f"❌ Erro ao exportar para CSV: {e}")
    
    def exportar_json(self, pedidos: List[Dict], filename: str = 'pedidos.json'):
        """Exporta pedidos para JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(pedidos, jsonfile, indent=2, ensure_ascii=False)
            print(f"✅ Pedidos exportados para: {filename}")
        except Exception as e:
            print(f"❌ Erro ao exportar para JSON: {e}")


def menu_interativo():
    """Menu interativo para o usuário"""
    print("\n" + "=" * 80)
    print("🍔 LEPAPON - GERENCIADOR DE PEDIDOS")
    print("=" * 80)
    print("\nOpções:")
    print("1. Listar todos os pedidos")
    print("2. Buscar pedido por ID")
    print("3. Filtrar por cliente")
    print("4. Filtrar por data")
    print("5. Filtrar por telefone (local)")
    print("6. Buscar por fone (API)")
    print("7. Exibir estatísticas")
    print("8. Exportar para CSV")
    print("9. Exportar para JSON")
    print("10. Criar novo pedido")
    print("0. Sair")
    print("=" * 80)


def main():
    """Função principal"""
    try:
        # Inicializa API
        api = LePaponAPI()
        manager = PedidosManager(api)
        
        print("\n✅ Conectado à API LePapon")
        print(f"🌐 URL: {api.base_url}")
        
        # Cache de pedidos
        pedidos_cache = None
        
        while True:
            menu_interativo()
            opcao = input("\n👉 Escolha uma opção: ").strip()
            
            if opcao == '0':
                print("\n👋 Até logo!")
                break
            
            elif opcao == '1':
                print("\n⏳ Carregando pedidos...")
                pedidos_cache = api.listar_pedidos()
                manager.exibir_pedidos(pedidos_cache)
            
            elif opcao == '2':
                pedido_id = input("Digite o ID do pedido: ").strip()
                if pedido_id.isdigit():
                    pedido = api.buscar_pedido(int(pedido_id))
                    if pedido:
                        manager.exibir_pedidos([pedido], detalhado=True)
                else:
                    print("❌ ID inválido")
            
            elif opcao == '3':
                if not pedidos_cache:
                    pedidos_cache = api.listar_pedidos()
                nome = input("Digite o nome do cliente: ").strip()
                filtrados = manager.filtrar_por_cliente(pedidos_cache, nome)
                manager.exibir_pedidos(filtrados)
            
            elif opcao == '4':
                if not pedidos_cache:
                    pedidos_cache = api.listar_pedidos()
                data = input("Digite a data (YYYY-MM-DD): ").strip()
                filtrados = manager.filtrar_por_data(pedidos_cache, data)
                manager.exibir_pedidos(filtrados)
            
            elif opcao == '5':
                if not pedidos_cache:
                    pedidos_cache = api.listar_pedidos()
                telefone = input("Digite o telefone: ").strip()
                filtrados = manager.filtrar_por_telefone(pedidos_cache, telefone)
                manager.exibir_pedidos(filtrados)
            
            elif opcao == '6':
                telefone = input("Digite o telefone para buscar na API: ").strip()
                pedidos_encontrados = api.buscar_por_fone(telefone)
                manager.exibir_pedidos(pedidos_encontrados, detalhado=True)

            elif opcao == '7':
                if not pedidos_cache:
                    pedidos_cache = api.listar_pedidos()
                manager.estatisticas(pedidos_cache)
            
            elif opcao == '8':
                if not pedidos_cache:
                    pedidos_cache = api.listar_pedidos()
                filename = input("Nome do arquivo (Enter para 'pedidos.csv'): ").strip()
                manager.exportar_csv(pedidos_cache, filename or 'pedidos.csv')
            
            elif opcao == '9':
                if not pedidos_cache:
                    pedidos_cache = api.listar_pedidos()
                filename = input("Nome do arquivo (Enter para 'pedidos.json'): ").strip()
                manager.exportar_json(pedidos_cache, filename or 'pedidos.json')
            
            elif opcao == '10':
                print("\n📝 Criar novo pedido:")
                try:
                    dados = {
                        'nome': input("Nome do cliente: ").strip(),
                        'fone': input("Telefone: ").strip(),
                        'id_Prod': int(input("ID do produto: ").strip()),
                        'qtd': float(input("Quantidade: ").strip()),
                        'observ': input("Observação: ").strip() or 'Normal'
                    }
                    pedido_criado = api.criar_pedido(dados)
                    if pedido_criado:
                        print(f"✅ Pedido criado com sucesso! ID: {pedido_criado.get('id')}")
                        pedidos_cache = None  # Invalida cache
                except ValueError:
                    print("❌ Dados inválidos")
            
            else:
                print("❌ Opção inválida")
            
            input("\n⏎ Pressione Enter para continuar...")
    
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")


if __name__ == "__main__":
    main()