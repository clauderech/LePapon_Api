import flet as ft
from models.recebido_api import RecebidoAPI
from models.clientes_api import ClientesAPI
import datetime
import pandas as pd
import os
import sys
import re
from reportlab.pdfgen import canvas as Canvas
from reportlab.lib.pagesizes import A4

# Importa as novas classes utilitárias
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../utils'))
from utils.base_view import BaseView
from utils.pdf_generator import PDFGenerator
from utils.common_utils import BASE_URL, parse_float, formatar_data, obter_nome_cliente, sanitize_filename

recebido_api = RecebidoAPI(BASE_URL)
clientes_api = ClientesAPI(BASE_URL)

def recebido_view(page: ft.Page):
    msg = ft.Text(visible=False)
    
    # Filtros de data (entrada manual)
    data_inicial = ft.TextField(
        label="Data Inicial",
        value=str(datetime.date.today()),
        on_change=lambda e: filtrar_recebidos_periodo(),
        width=140,
        hint_text="AAAA-MM-DD"
    )
    data_final = ft.TextField(
        label="Data Final",
        value=str(datetime.date.today()),
        on_change=lambda e: filtrar_recebidos_periodo(),
        width=140,
        hint_text="AAAA-MM-DD"
    )
    
    # Caixa de seleção de clientes
    try:
        clientes = clientes_api.get_all()
        if not isinstance(clientes, list):
            clientes = [clientes] if clientes else []
    except Exception:
        clientes = []
    opcoes_clientes = [ft.dropdown.Option(text=f"{c.get('id', '')} - {c.get('nome', '')} - {c.get('sobrenome', '')}", key=str(c.get('id', ''))) for c in clientes if isinstance(c, dict)]
    dropdown_clientes = ft.Dropdown(
        options=opcoes_clientes,
        label="Selecionar Cliente",
        width=350,
        on_change=lambda e: filtrar_recebidos_periodo()
    )
    
    total_recebidos_label = ft.Text("Total do período: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM, width=250)
    tabela_ref = ft.Ref[ft.DataTable]()

    def filtrar_recebidos_periodo():
        di = data_inicial.value
        df = data_final.value
        cliente_id = dropdown_clientes.value
        
        if not di or not df:
            return
            
        di_str = str(di)
        df_str = str(df)
        
        try:
            recebidos = recebido_api.get_all()
            if not isinstance(recebidos, list):
                recebidos = [recebidos] if recebidos else []
            
            # Converte para DataFrame
            recebidos_df = pd.DataFrame(recebidos)
            
            if recebidos_df.empty:
                recebidos_periodo = recebidos_df
            else:
                # Filtra por data
                recebidos_periodo = recebidos_df[(recebidos_df['data'] >= di_str) & (recebidos_df['data'] <= df_str)]
                
                # Filtra por cliente se selecionado
                if cliente_id:
                    recebidos_periodo = recebidos_periodo[recebidos_periodo['id_cliente'].astype(str) == cliente_id]
                
                # Ordena por data
                recebidos_periodo = recebidos_periodo.sort_values(['data', 'hora'], ascending=[True, True])
            
            # Campos para exibir
            campos_exibir = ['data', 'hora', 'nome_cliente', 'valor']
            colunas_legenda = {
                'data': 'Data',
                'hora': 'Hora',
                'nome_cliente': 'Cliente',
                'valor': 'Valor'
            }
            
            # Formata a data para exibição
            if not recebidos_periodo.empty:
                recebidos_periodo = recebidos_periodo.copy()
                if 'data' in recebidos_periodo.columns:
                    def formatar_data(d):
                        try:
                            data_str = str(d).split('T')[0]
                            return datetime.datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except Exception:
                            return d or ''
                    recebidos_periodo['data'] = recebidos_periodo['data'].apply(formatar_data)
                
                # Adiciona nome do cliente
                if 'id_cliente' in recebidos_periodo.columns:
                    def obter_nome_cliente(cliente_id):
                        cliente = next((c for c in clientes if str(c.get('id', '')) == str(cliente_id)), None)
                        if cliente:
                            return f"{cliente.get('nome', '')} {cliente.get('sobrenome', '')}"
                        return f"Cliente {cliente_id}"
                    recebidos_periodo['nome_cliente'] = recebidos_periodo['id_cliente'].apply(obter_nome_cliente)
            
            # Seleciona apenas os campos desejados
            if not recebidos_periodo.empty and all(campo in recebidos_periodo.columns for campo in campos_exibir):
                recebidos_periodo = recebidos_periodo[campos_exibir]
                columns = [ft.DataColumn(ft.Text(colunas_legenda[c])) for c in campos_exibir]
            else:
                columns = [ft.DataColumn(ft.Text("Data"))]
            
            rows = []
            total = 0.0
            
            if not recebidos_periodo.empty:
                for _, recebido in recebidos_periodo.iterrows():
                    row = [ft.DataCell(ft.Text(str(recebido.get(c, "")))) for c in campos_exibir]
                    rows.append(ft.DataRow(row))
                    try:
                        total += float(str(recebido.get("valor", 0)).replace(",", "."))
                    except:
                        pass
            
            if not rows:
                rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
            
            tabela_ref.current.columns = columns
            tabela_ref.current.rows = rows
            total_recebidos_label.value = f"Total do período: {total:.2f}"
            page.update()
            
        except Exception as e:
            msg.value = f"Erro ao buscar recebidos: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Inicializa tabela vazia
    tabela = ft.DataTable(ref=tabela_ref, columns=[ft.DataColumn(ft.Text("Data"))], rows=[])
    # Carrega recebidos do dia atual ao abrir
    filtrar_recebidos_periodo()

    filtro_nome = ft.TextField(
        label="Filtrar cliente por nome",
        width=200,
        on_change=lambda e: filtrar_opcoes_clientes()
    )
    
    def filtrar_opcoes_clientes():
        nome_filtro = (filtro_nome.value or "").lower()
        dropdown_clientes.options = [
            ft.dropdown.Option(text=f"{c.get('id', '')} - {c.get('nome', '')} - {c.get('sobrenome', '')}", key=str(c.get('id', '')))
            for c in clientes if isinstance(c, dict) and nome_filtro in str(c.get('nome', '')).lower()
        ]
        page.update()

    def exportar_pdf():
        try:
            # Usa os mesmos dados filtrados da tabela
            di = data_inicial.value
            df = data_final.value
            cliente_id = dropdown_clientes.value
            di_str = str(di)
            df_str = str(df)
            
            recebidos = recebido_api.get_all()
            if not isinstance(recebidos, list):
                recebidos = [recebidos] if recebidos else []
            
            recebidos_df = pd.DataFrame(recebidos)
            
            if not recebidos_df.empty:
                recebidos_periodo = recebidos_df[(recebidos_df['data'] >= di_str) & (recebidos_df['data'] <= df_str)]
                
                if cliente_id:
                    recebidos_periodo = recebidos_periodo[recebidos_periodo['id_cliente'].astype(str) == cliente_id]
                
                recebidos_periodo = recebidos_periodo.sort_values(['data', 'hora'], ascending=[True, True])
            else:
                recebidos_periodo = recebidos_df
            
            # Campos para o PDF
            campos_exibir = ['data', 'hora', 'nome_cliente', 'valor']
            colunas_legenda = {
                'data': 'Data',
                'hora': 'Hora',
                'nome_cliente': 'Cliente',
                'valor': 'Valor'
            }
            
            if not recebidos_periodo.empty:
                recebidos_periodo = recebidos_periodo.copy()
                if 'data' in recebidos_periodo.columns:
                    def formatar_data(d):
                        try:
                            data_str = str(d).split('T')[0]
                            return datetime.datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except Exception:
                            return d or ''
                    recebidos_periodo['data'] = recebidos_periodo['data'].apply(formatar_data)
                
                # Adiciona nome do cliente
                if 'id_cliente' in recebidos_periodo.columns:
                    def obter_nome_cliente(cliente_id):
                        cliente = next((c for c in clientes if str(c.get('id', '')) == str(cliente_id)), None)
                        if cliente:
                            return f"{cliente.get('nome', '')} {cliente.get('sobrenome', '')}"
                        return f"Cliente {cliente_id}"
                    recebidos_periodo['nome_cliente'] = recebidos_periodo['id_cliente'].apply(obter_nome_cliente)
                
                # Geração do PDF
                if cliente_id:
                    cliente_nome = next((c.get('nome', '') + ' ' + c.get('sobrenome', '') for c in clientes if str(c.get('id', '')) == str(cliente_id)), f'cliente_{cliente_id}')
                else:
                    cliente_nome = 'todos_clientes'
                
                # Remove caracteres inválidos do nome do cliente para pasta
                cliente_nome_pasta = re.sub(r'[^a-zA-Z0-9_\-]', '_', cliente_nome)
                pasta_destino = os.path.join(os.path.dirname(__file__), '../Recebidos', cliente_nome_pasta)
                os.makedirs(pasta_destino, exist_ok=True)
                data_pdf = datetime.datetime.now().strftime('%Y-%m-%d')
                pdf_path = os.path.join(pasta_destino, f'{data_pdf}.pdf')
                
                c = Canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                
                # Cabeçalho personalizado
                logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../acents/L.png'))
                try:
                    c.drawImage(logo_path, 40, height-100, width=60, height=60, preserveAspectRatio=True, mask='auto')
                except Exception:
                    c.setFont("Helvetica", 8)
                    c.drawString(40, height-100, f"[Logo não encontrado: {logo_path}]")
                
                c.setFont("Helvetica-Bold", 16)
                c.drawString(110, height-60, "LePapon Lanches - Claudemir")
                c.setFont("Helvetica", 10)
                c.drawString(110, height-80, "Endereço: João Venâncio Girarde, nº 260")
                c.drawString(110, height-95, "CNPJ: 33.794.253/0001-33   Fone: (55) 5499-2635135")
                
                # Data do relatório
                c.setFont("Helvetica", 10)
                c.drawString(400, height-60, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}")
                
                # Título do relatório
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, height-120, f"Relatório de Recebimentos: {cliente_nome}")
                c.setFont("Helvetica", 10)
                y = height-150
                
                # Definição das larguras das colunas
                col_widths = [70, 50, 250, 70]  # data, hora, nome_cliente, valor
                x_positions = [40]
                for w in col_widths[:-1]:
                    x_positions.append(x_positions[-1] + w)
                
                # Cabeçalho
                for i, campo in enumerate(campos_exibir):
                    c.drawString(x_positions[i], y, colunas_legenda[campo])
                y -= 20
                
                # Dados
                for _, row in recebidos_periodo.iterrows():
                    for i, campo in enumerate(campos_exibir):
                        c.drawString(x_positions[i], y, str(row.get(campo, "")))
                    y -= 18
                    if y < 60:
                        c.showPage()
                        y = height-40
                
                # Escreve o total no final do PDF
                if y < 80:
                    c.showPage()
                    y = height-40
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y-10, f"Total do período: R$ {recebidos_periodo['valor'].astype(float).sum():.2f}")
                c.save()
                
                msg.value = f"PDF gerado em: {pdf_path}"
                msg.color = "green"
            else:
                msg.value = "Nenhum dado para exportar."
                msg.color = "red"
            
            msg.visible = True
            page.update()
            
        except Exception as e:
            msg.value = f"Erro ao exportar PDF: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()

    botao_pdf = ft.ElevatedButton("Exportar PDF", on_click=lambda e: exportar_pdf())

    return ft.Column([
        ft.Text("Lista de Recebimentos", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            data_inicial,
            data_final,
            filtro_nome,
            dropdown_clientes
        ]),
        ft.Row([
            botao_pdf,
            total_recebidos_label
        ]),
        ft.Column(controls=[
            tabela,
            ft.Divider(),
            msg
        ], scroll=ft.ScrollMode.ALWAYS, height=600, width=900),
    ])
