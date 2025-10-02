import mysql.connector
from datetime import date, timedelta

# Configurações do banco de dados
config = {
    'user': 'claude',
    'password': 'Corech260Re@',
    'host': '192.168.15.3',
    'database': 'LePapon_Vendas',
    'raise_on_warnings': True
}

def main():
    data_final = date.today() - timedelta(days=1)  # ontem
    data_inicial = data_final - timedelta(days=5)  # últimos 6 dias, sem hoje

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Vendas
    cursor.execute("""
        SELECT IFNULL(SUM(sub_total), 0) FROM Vendas WHERE data BETWEEN %s AND %s
    """, (data_inicial, data_final))
    total_vendas = cursor.fetchone()

    # Crediario
    cursor.execute("""
        SELECT IFNULL(SUM(sub_total), 0) FROM Crediario WHERE data BETWEEN %s AND %s
    """, (data_inicial, data_final))
    total_crediario = cursor.fetchone()

    # Recebido
    cursor.execute("""
        SELECT IFNULL(SUM(valor), 0) FROM recebido WHERE data BETWEEN %s AND %s
    """, (data_inicial, data_final))
    total_recebido = cursor.fetchone()

    # Inserir na tabela Controle_Semanal
    '''cursor.execute("""
        INSERT INTO Controle_Semanal (data_inicial, data_final, total_vendas, total_crediario, total_recebido)
        VALUES (%s, %s, %s, %s, %s)
    """, (data_inicial, data_final, total_vendas, total_crediario, total_recebido))
    conn.commit()'''
    print(f"Total Vendas: {total_vendas}")
    print(f"Total Crediario: {total_crediario}")
    print(f"Total Recebido: {total_recebido}")
    print(f"Controle semanal inserido: {data_inicial} a {data_final}")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
