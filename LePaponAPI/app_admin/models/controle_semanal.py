from models.vendas_api import VendasAPI
from models.crediario_api import CrediarioAPI
from models.recebido_api import RecebidoAPI
from models.despesas_diarias_api import DespesasDiariasAPI
from models.controle_semanal_api import ControleSemanalAPI
from datetime import date, timedelta

class ControleSemanal:
    def consultar_periodo(self, data_inicio, data_fim):
        """
        Consulta totais de vendas, crediário, recebido e despesas para um período informado.
        Retorna:
            dict com os totais encontrados
        """
        vendas = self.vendas_api.get_sum_period(data_inicio, data_fim)
        crediario = self.crediario_api.get_sum_period(data_inicio, data_fim)
        recebido = self.recebido_api.get_sum_period(data_inicio, data_fim)
        despesas = self.despesas_diarias_api.get_sum_period(data_inicio, data_fim)

        def soma_valor(obj, campo):
            if isinstance(obj, dict):
                return float(obj.get(campo, 0) or 0)
            return 0

        return {
            'total_vendas': soma_valor(vendas, 'total'),
            'total_crediario': soma_valor(crediario, 'total'),
            'total_recebido': soma_valor(recebido, 'total'),
            'total_despesas': soma_valor(despesas, 'total'),
        }
    def __init__(self, base_url):
        self.vendas_api = VendasAPI(base_url)
        self.crediario_api = CrediarioAPI(base_url)
        self.recebido_api = RecebidoAPI(base_url)
        self.despesas_diarias_api = DespesasDiariasAPI(base_url)

    def consultar(self):
        """
        Consulta totais de vendas, crediário, recebido e despesas dos últimos 7 dias (excluindo hoje).
        Retorna:
            dict com os totais encontrados
        """
        vendas = self.vendas_api.get_last7days_sum()
        crediario = self.crediario_api.get_last7days_sum()
        recebido = self.recebido_api.get_last7days_sum()
        despesas = self.despesas_diarias_api.get_last7days_sum()

        def soma_valor(obj, campo):
            if isinstance(obj, dict):
                return float(obj.get(campo, 0) or 0)
            return 0

        return {
            'total_vendas': soma_valor(vendas, 'total'),
            'total_crediario': soma_valor(crediario, 'total'),
            'total_recebido': soma_valor(recebido, 'total'),
            'total_despesas': soma_valor(despesas, 'total'),
        }
    
    def registrar(self):
        """
        Realiza a consulta e registra o resultado no banco via ControleSemanalAPI.
        Retorna:
            dict com o resultado inserido
        """
        resultado = self.consultar()
        api = ControleSemanalAPI(self.vendas_api.base_url)
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        data_final = ontem.isoformat()
        data_inicial = (ontem - timedelta(days=6)).isoformat()
        payload = {
            'data_inicial': data_inicial,
            'data_final': data_final,
            'total_vendas': resultado['total_vendas'],
            'total_crediario': resultado['total_crediario'],
            'total_recebido': resultado['total_recebido'],
            'total_despesas': resultado['total_despesas']
        }
        return api.create(payload)

# Exemplo de uso:
# controle = ControleSemanal('http://lepapon.api:3000')
# resultado = controle.consultar()
# print(resultado)
