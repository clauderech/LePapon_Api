"""
Classe base para views com funcionalidades comuns
"""
import flet as ft
import datetime
import pandas as pd
from utils.common_utils import BASE_URL, formatar_data, obter_nome_cliente

class BaseView:
    """Classe base para views com filtros e funcionalidades comuns"""
    
    def __init__(self, page, api_instance, clientes_api=None):
        self.page = page
        self.api = api_instance
        self.clientes_api = clientes_api
        self.msg = ft.Text(visible=False)
        
        # Busca clientes se disponível
        self.clientes = []
        if clientes_api:
            try:
                self.clientes = clientes_api.get_all()
                if not isinstance(self.clientes, list):
                    self.clientes = [self.clientes] if self.clientes else []
            except Exception:
                self.clientes = []
    
    def criar_filtros_data(self, on_change_callback):
        """Cria filtros de data inicial e final"""
        data_hoje = str(datetime.date.today())
        
        data_inicial = ft.TextField(
            label="Data Inicial",
            value=data_hoje,
            on_change=lambda e: on_change_callback(),
            width=140,
            hint_text="AAAA-MM-DD"
        )
        
        data_final = ft.TextField(
            label="Data Final",
            value=data_hoje,
            on_change=lambda e: on_change_callback(),
            width=140,
            hint_text="AAAA-MM-DD"
        )
        
        return data_inicial, data_final
    
    def criar_dropdown_clientes(self, on_change_callback):
        """Cria dropdown de seleção de clientes"""
        opcoes_clientes = [
            ft.dropdown.Option(
                text=f"{c.get('id', '')} - {c.get('nome', '')} - {c.get('sobrenome', '')}", 
                key=str(c.get('id', ''))
            ) 
            for c in self.clientes if isinstance(c, dict)
        ]
        
        dropdown_clientes = ft.Dropdown(
            options=opcoes_clientes,
            label="Selecionar Cliente",
            width=350,
            on_change=lambda e: on_change_callback()
        )
        
        return dropdown_clientes
    
    def criar_filtro_nome_cliente(self, dropdown_clientes):
        """Cria filtro por nome do cliente"""
        filtro_nome = ft.TextField(
            label="Filtrar cliente por nome",
            width=200,
            on_change=lambda e: self.filtrar_opcoes_clientes(filtro_nome, dropdown_clientes)
        )
        
        return filtro_nome
    
    def filtrar_opcoes_clientes(self, filtro_nome, dropdown_clientes):
        """Filtra opções do dropdown por nome"""
        nome_filtro = (filtro_nome.value or "").lower()
        dropdown_clientes.options = [
            ft.dropdown.Option(
                text=f"{c.get('id', '')} - {c.get('nome', '')} - {c.get('sobrenome', '')}", 
                key=str(c.get('id', ''))
            )
            for c in self.clientes 
            if isinstance(c, dict) and nome_filtro in str(c.get('nome', '')).lower()
        ]
        self.page.update()
    
    def processar_dados_periodo(self, data_inicial, data_final, cliente_id=None, campo_cliente='id_cliente'):
        """Processa dados de um período específico"""
        try:
            dados = self.api.get_all()
            if not isinstance(dados, list):
                dados = [dados] if dados else []
            
            # Converte para DataFrame
            df = pd.DataFrame(dados)
            
            if df.empty:
                return df
            
            # Filtra por data
            di_str = str(data_inicial)
            df_str = str(data_final)
            df_filtrado = df[(df['data'] >= di_str) & (df['data'] <= df_str)]
            
            # Filtra por cliente se selecionado
            if cliente_id:
                df_filtrado = df_filtrado[df_filtrado[campo_cliente].astype(str) == cliente_id]
            
            # Ordena por data
            if 'hora' in df_filtrado.columns:
                df_filtrado = df_filtrado.sort_values(['data', 'hora'], ascending=[True, True])
            else:
                df_filtrado = df_filtrado.sort_values(['data'], ascending=[True])
            
            return df_filtrado
            
        except Exception as e:
            self.mostrar_mensagem(f"Erro ao buscar dados: {e}", "red")
            return pd.DataFrame()
    
    def formatar_dados_exibicao(self, df, campos_exibir):
        """Formata dados para exibição na tabela"""
        if df.empty:
            return df
        
        df_copia = df.copy()
        
        # Formata data
        if 'data' in df_copia.columns:
            df_copia['data'] = df_copia['data'].apply(formatar_data)
        
        # Adiciona nome do cliente se necessário
        if 'id_cliente' in df_copia.columns and 'nome_cliente' not in df_copia.columns:
            df_copia['nome_cliente'] = df_copia['id_cliente'].apply(
                lambda x: obter_nome_cliente(self.clientes, x)
            )
        
        return df_copia[campos_exibir] if all(campo in df_copia.columns for campo in campos_exibir) else df_copia
    
    def criar_tabela_datatable(self, df, campos_exibir, colunas_legenda):
        """Cria uma DataTable do Flet"""
        if df.empty or not all(campo in df.columns for campo in campos_exibir):
            columns = [ft.DataColumn(ft.Text("Data"))]
            rows = [ft.DataRow([ft.DataCell(ft.Text(""))])]
        else:
            columns = [ft.DataColumn(ft.Text(colunas_legenda[c])) for c in campos_exibir]
            rows = []
            
            for _, row in df.iterrows():
                cells = [ft.DataCell(ft.Text(str(row.get(c, "")))) for c in campos_exibir]
                rows.append(ft.DataRow(cells))
            
            if not rows:
                rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
        
        return columns, rows
    
    def calcular_total(self, df, campo_valor='valor'):
        """Calcula o total de uma coluna de valores"""
        if df.empty or campo_valor not in df.columns:
            return 0.0
        
        total = 0.0
        for _, row in df.iterrows():
            try:
                total += float(str(row.get(campo_valor, 0)).replace(",", "."))
            except:
                pass
        
        return total
    
    def mostrar_mensagem(self, texto, cor="blue"):
        """Mostra mensagem para o usuário"""
        self.msg.value = texto
        self.msg.color = cor
        self.msg.visible = True
        self.page.update()
    
    def limpar_mensagem(self):
        """Limpa a mensagem"""
        self.msg.value = ""
        self.msg.visible = False
        self.page.update()
