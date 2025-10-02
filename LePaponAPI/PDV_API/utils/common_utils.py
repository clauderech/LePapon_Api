"""
Utilitários comuns para todas as views do sistema
"""
import datetime

# Configuração base da API
BASE_URL = "http://lepapon.api:3000"

def parse_float(val):
    """
    Converte um valor para float, tratando vírgulas como pontos decimais
    """
    try:
        return float(str(val).replace(',', '.'))
    except:
        return 0.0

def formatar_data(d):
    """
    Formata uma data ISO para DD/MM/YYYY
    """
    try:
        data_str = str(d).split('T')[0]
        return datetime.datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return d or ''

def get_current_datetime():
    """
    Retorna data e hora atuais formatadas
    """
    agora = datetime.datetime.now()
    return {
        'data': agora.strftime('%Y-%m-%d'),
        'hora': agora.strftime('%H:%M:%S'),
        'data_pdf': agora.strftime('%Y-%m-%d'),
        'data_display': agora.strftime('%d/%m/%Y')
    }

def sanitize_filename(nome):
    """
    Remove caracteres inválidos de nomes de arquivo
    """
    import re
    return re.sub(r'[^a-zA-Z0-9_\-]', '_', nome)

def obter_nome_cliente(clientes, cliente_id):
    """
    Obtém o nome completo do cliente pelo ID
    """
    cliente = next((c for c in clientes if str(c.get('id', '')) == str(cliente_id)), None)
    if cliente:
        return f"{cliente.get('nome', '')} {cliente.get('sobrenome', '')}"
    return f"Cliente {cliente_id}"
