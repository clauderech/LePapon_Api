from models.vendas_api import VendasAPI
from models.crediario_api import CrediarioAPI
from models.recebido_api import RecebidoAPI
from models.despesas_diarias_api import DespesasDiariasAPI
from models.controle_diario_api import ControleDiarioAPI
from datetime import datetime

class ControleDiario:
    def __init__(self, base_url):
        self.vendas_api = VendasAPI(base_url)
        self.crediario_api = CrediarioAPI(base_url)
        self.recebido_api = RecebidoAPI(base_url)
        self.despesas_diarias_api = DespesasDiariasAPI(base_url)

    def consultar(self, data):
        """
        Consulta totais de vendas, crediário, recebido e despesas para uma data específica.
        Parâmetros:
            data (str): data no formato 'YYYY-MM-DD'
        Retorna:
            dict com os totais encontrados
        """
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Data inválida. Use o formato YYYY-MM-DD.")

        vendas = self.vendas_api.get_by_data(data)
        crediario = self.crediario_api.get_by_data(data)
        recebido = self.recebido_api.get_by_data(data)
        despesas = self.despesas_diarias_api.get_by_data(data)

        def soma_valor(lista, campo):
            if isinstance(lista, dict):
                lista = [lista]
            return sum(float(item.get(campo, 0) or 0) for item in lista if item)

        return {
            'total_vendas': soma_valor(vendas, 'sub_total'),
            'total_crediario': soma_valor(crediario, 'sub_total'),
            'total_recebido': soma_valor(recebido, 'valor'),
            'total_despesas': soma_valor(despesas, 'valor'),
        }
    
    def registrar(self, data):
        """
        Realiza a consulta e registra o resultado no banco via ControleDiarioAPI.
        Parâmetros:
            data (str): data no formato 'YYYY-MM-DD'
        Retorna:
            dict com o resultado inserido
        """
        resultado = self.consultar(data)
        api = ControleDiarioAPI(self.vendas_api.base_url)
        payload = {
            'data': data,
            'total_vendas': resultado['total_vendas'],
            'total_crediario': resultado['total_crediario'],
            'total_recebido': resultado['total_recebido'],
            'total_despesas': resultado['total_despesas']
        }
        return api.create(payload)
    

# Exemplo de uso:
# controle = ControleDiario('http://lepapon.api:3000')
# resultado = controle.consultar('2025-06-18')
# print(resultado)
