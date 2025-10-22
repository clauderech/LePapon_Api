import requests
import json
import asyncio
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Any
from models.numPedidoModel import NumPedidoAPI
from models.pedidosModel import PedidoAPI

class PedidoManager:
    """
    Gerenciador centralizado para operações de pedidos.
    Combina funcionalidades de busca, registro e processamento de pedidos.
    """
    
    def __init__(self, local_base_url: str = "http://lepapon.com.br:3000/api"):
        self.base_url = local_base_url
        self.num_pedido_api = NumPedidoAPI()
        self.pedido_api = PedidoAPI()
    
    # ===== MÉTODOS UTILITÁRIOS =====
    
    @staticmethod
    def formatar_data(data: str) -> str:
        """Formata data ISO para formato YYYY-MM-DD."""
        try:
            return datetime.fromisoformat(data.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except Exception:
            return data
    
    @staticmethod
    def formatar_hora(hora: str) -> str:
        """Formata hora para formato HH:MM:SS."""
        try:
            if "T" in hora:
                return datetime.fromisoformat(hora.replace("Z", "+00:00")).strftime("%H:%M:%S")
            else:
                return hora if len(hora.split(":")) == 3 else hora + ":00"
        except Exception:
            return hora
    
    def montar_pedido_payload(self, id_cliente: int, num_pedido: int, 
                            id_order_pedido: int, pedido: Dict, 
                            data: str, hora: str) -> Dict[str, Any]:
        """Monta payload completo para um pedido."""
        return {
            "id_cliente": id_cliente,
            "numPedido": num_pedido,
            "idOrderPedido": id_order_pedido,
            "id_Prod": pedido.get("id_Prod"),
            "qtd": pedido.get("qtd"),
            "observ": pedido.get("observ", ""),
            "V_unit": pedido.get("Valor_Prod"),
            "data": self.formatar_data(data),
            "hora": self.formatar_hora(hora)
        }
    
    # ===== MÉTODOS DE BUSCA E VERIFICAÇÃO =====
    
    def buscar_numero_pedido(self, fone: str) -> Optional[Dict]:
        """Busca o número do pedido pelo telefone na API local."""
        url = f"{self.base_url}/numpedidos/fone/{fone}"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
    
    def buscar_cliente_por_fone(self, fone: str) -> Optional[Dict]:
        """Busca um cliente pelo telefone na API local."""
        url = f"{self.base_url}/numpedidos/fone/{fone}"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            if isinstance(data, list) and data:
                return data[0]
            elif isinstance(data, dict):
                return data
            else:
                return None
        except Exception as e:
            print(f"Erro ao buscar cliente para o telefone {fone}: {e}")
            return None
    
    def pedido_existe_localmente(self, pedido_payload: Dict, num_pedido: Optional[int] = None) -> bool:
        """Verifica se o pedido já existe no servidor local para evitar duplicidade."""
        if not num_pedido:
            return False
            
        url_temp = f"{self.base_url}/numpedidos/{num_pedido}"
        try:
            resp_temp = requests.get(url_temp)
            resp_temp.raise_for_status()
            pedidos_temp = resp_temp.json()
            
            # Verifica se já existe pedido com mesma data e hora
            existe_temp = any(
                p.get("data") == pedido_payload["data"] and 
                p.get("hora") == pedido_payload["hora"] 
                for p in pedidos_temp
            )
            
            return existe_temp
        except Exception as e:
            print(f"Erro ao buscar pedidos temporários: {e}")
            return False
    
    # ===== MÉTODOS DE REGISTRO =====
    
    def registrar_numero_pedido(self, payload: Dict) -> Optional[Dict]:
        """Registra um novo número de pedido na API local."""
        return self.num_pedido_api.criar_num_pedido(payload)
    
    def registrar_ordem_pedido(self, payload: Dict) -> Optional[Dict]:
        """Registra uma nova ordem de pedido na API local."""
        url = f"{self.base_url}/orderpedidos"
        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro ao registrar ordem de pedido: {e}")
            return None
    
    def salvar_pedido_local(self, endpoint: str, item: Dict) -> None:
        """Salva um pedido no servidor local."""
        if endpoint == "pedidos":
            result = self.pedido_api.criar_pedido(item)
            if not result:
                print(f"Erro ao salvar pedido localmente - Payload: {item}")
        else:
            url_local = f"{self.base_url}/{endpoint}"
            try:
                r = requests.post(url_local, json=item)
                r.raise_for_status()
            except Exception as e:
                print(f"Erro ao salvar pedido localmente: {e} - Payload: {item}")
    
    # ===== MÉTODOS ASSÍNCRONOS =====
    
    async def async_buscar_numero_pedido(self, fone: str) -> Optional[Dict]:
        """Versão assíncrona de buscar_numero_pedido."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.buscar_numero_pedido, fone)
    
    async def async_registrar_numero_pedido(self, payload: Dict) -> Optional[Dict]:
        """Versão assíncrona de registrar_numero_pedido."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.registrar_numero_pedido, payload)
    
    async def async_buscar_cliente_por_fone(self, fone: str) -> Optional[Dict]:
        """Versão assíncrona de buscar_cliente_por_fone."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.buscar_cliente_por_fone, fone)
    
    async def async_registrar_ordem_pedido(self, payload: Dict) -> Optional[Dict]:
        """Versão assíncrona de registrar_ordem_pedido."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.registrar_ordem_pedido, payload)
    
    async def async_salvar_pedido_local(self, endpoint: str, item: Dict) -> None:
        """Versão assíncrona de salvar_pedido_local."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.salvar_pedido_local, endpoint, item)
    
    async def async_pedido_existe_localmente(self, pedido_payload: Dict, num_pedido: Optional[int] = None) -> bool:
        """Versão assíncrona de pedido_existe_localmente."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.pedido_existe_localmente, pedido_payload, num_pedido)
    
    # ===== PROCESSAMENTO EM LOTE =====
    
    async def processar_e_salvar_pedidos(self, pedidos: List[Dict], id_cliente: int, 
                                       num_pedido: int, id_order_pedido: int, 
                                       hora_item: str, data: str, 
                                       df_produtos: Optional[pd.DataFrame] = None) -> None:
        """
        Processa e salva uma lista de pedidos usando pandas para merge com produtos.
        """
        if df_produtos is not None and not df_produtos.empty:
            df_pedidos = pd.DataFrame(pedidos)
            df_merged = pd.merge(df_pedidos, df_produtos, left_on="id_Prod", right_on="id_Prod", how="left")
            
            for _, pedido in df_merged.iterrows():
                data_pedido = pedido.get("data", data)
                hora_pedido = pedido.get("hora", hora_item)
                pedido_dict = pedido.to_dict()
                payload = self.montar_pedido_payload(
                    id_cliente, num_pedido, id_order_pedido, 
                    pedido_dict, data_pedido, hora_pedido
                )
                await self.async_salvar_pedido_local("pedidos", payload)
        else:
            print("DataFrame de produtos está vazio ou não foi fornecido. Não será possível processar os pedidos.")
