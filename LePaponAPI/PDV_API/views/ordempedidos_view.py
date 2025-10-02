import flet as ft
from flet import Icons
import pandas as pd
from urllib.parse import quote
import requests
from models.ordempedidos_api import OrdemPedidosAPI
from models.numpedidos_api import NumPedidosAPI
from datetime import datetime
from views.tema_0_0_0 import texto_titulo, aplicar_tema, botao_acao
from config import BASE_URL
from utils.ui_components import create_filter_field

ordempedidos_api = OrdemPedidosAPI(BASE_URL)

def ordempedidos_view(page: ft.Page):
    # Mensagem de feedback para o usuário
    msg = ft.Text(visible=False)
    aplicar_tema(page)
    
    # Estado unificado da seleção
    ordem_selecionada_data = None
    loading_indicator = ft.ProgressRing(visible=False, width=16, height=16)

    def show_message(text: str, color: str = "blue", duration: int = 3):
        """Mostra mensagem temporária para o usuário"""
        msg.value = text
        msg.color = color
        msg.visible = True
        page.update()

    def validate_api_data(data, expected_fields=None):
        """Valida estrutura de dados da API"""
        if not isinstance(data, list):
            data = [data] if data else []
        
        if expected_fields:
            valid_data = []
            for item in data:
                if isinstance(item, dict) and all(field in item for field in expected_fields):
                    valid_data.append(item)
            return valid_data
        return data

    # Carregamento robusto dos dados
    pedidos_data = []
    ordem_data = []
    api_errors = []

    # Busca números de pedidos com tratamento específico
    numpedidos_api = NumPedidosAPI(BASE_URL)
    loading_indicator.visible = True
    page.update()
    
    try:
        pedidos_raw = numpedidos_api.get_all()
        pedidos_data = validate_api_data(pedidos_raw, ['id', 'nome'])
        if not pedidos_data and pedidos_raw:
            api_errors.append("Dados de pedidos em formato inválido")
    except (requests.RequestException, requests.ConnectionError) as e:
        api_errors.append(f"Erro de conexão ao buscar pedidos: {e}")
    except Exception as e:
        api_errors.append(f"Erro inesperado ao buscar pedidos: {e}")

    # Busca ordens de pedidos com tratamento específico
    try:
        ordem_raw = ordempedidos_api.get_all()
        ordem_data = validate_api_data(ordem_raw, ['id', 'numPedido'])
        if not ordem_data and ordem_raw:
            api_errors.append("Dados de ordens em formato inválido")
    except (requests.RequestException, requests.ConnectionError) as e:
        api_errors.append(f"Erro de conexão ao buscar ordens: {e}")
    except Exception as e:
        api_errors.append(f"Erro inesperado ao buscar ordens: {e}")

    loading_indicator.visible = False
    
    # Mostra erros se houver, mas continua carregamento
    if api_errors:
        show_message(f"⚠️ Problemas no carregamento: {'; '.join(api_errors)}", "orange")

    # Cria DataFrames com tratamento seguro
    df_merged = pd.DataFrame()
    df_pedidos = pd.DataFrame()
    df_ordem = pd.DataFrame()
    
    try:
        df_ordem = pd.DataFrame(ordem_data) if ordem_data else pd.DataFrame()
        df_pedidos = pd.DataFrame(pedidos_data) if pedidos_data else pd.DataFrame()
        
        # Merge seguro com verificação de colunas
        if not df_ordem.empty and not df_pedidos.empty:
            if 'numPedido' in df_ordem.columns and 'id' in df_pedidos.columns:
                df_merged = pd.merge(df_ordem, df_pedidos, left_on="numPedido", right_on="id", how="left", suffixes=("", "_pedido"))
            else:
                df_merged = df_ordem
                show_message("⚠️ Estrutura de dados incompatível - merge não realizado", "orange")
        else:
            df_merged = df_ordem
            
    except Exception as e:
        show_message(f"❌ Erro ao processar dados: {e}", "red")
        df_merged = pd.DataFrame()
    
    def selecionar_linha(e, row_data):
        """Seleciona linha com tratamento seguro de race conditions"""
        nonlocal ordem_selecionada_data
        
        try:
            # Limpa seleção anterior com verificação segura
            if tabela_ref.current and hasattr(tabela_ref.current, 'rows') and tabela_ref.current.rows:
                for row in tabela_ref.current.rows:
                    try:
                        if hasattr(row, 'selected'):
                            row.selected = False
                    except (AttributeError, RuntimeError):
                        # Ignora erros se linha foi removida/modificada
                        continue
                
            # Seleciona nova linha com verificação
            try:
                if hasattr(e.control, 'selected'):
                    e.control.selected = True
            except (AttributeError, RuntimeError):
                pass  # Falha graciosamente se elemento foi modificado
                
            ordem_selecionada_data = row_data
            
            # Atualiza mensagem de feedback
            show_message(f"✅ Ordem selecionada: ID {row_data.get('id', '')}, Pedido {row_data.get('numPedido', '')}", "blue")
            
        except Exception as e:
            show_message(f"⚠️ Erro na seleção: {e}", "orange")

    def ir_para_produtos_todos(e):
        """Navega para produtos com validação rigorosa"""
        # Exige seleção explícita - sem fallback automático
        if not ordem_selecionada_data:
            show_message("❌ Selecione uma ordem primeiro clicando na tabela", "red")
            return
            
        selected_ordem = ordem_selecionada_data
        
        # Valida dados essenciais
        num_pedido_id = selected_ordem.get('numPedido')
        id_ordem_val = selected_ordem.get('id')
        id_cliente_val = selected_ordem.get('id_cliente')
        
        if not all([num_pedido_id, id_ordem_val]):
            show_message("❌ Dados da ordem incompletos", "red")
            return
            
        # Busca dados do pedido de forma eficiente
        pedido = None
        try:
            # Cria índice para busca O(1) ao invés de O(n)
            pedidos_dict = {str(row.get('id', '')): row for _, row in df_pedidos.iterrows()} if not df_pedidos.empty else {}
            pedido_data = pedidos_dict.get(str(num_pedido_id))
            
            if pedido_data is not None:
                # Valida se é Series do pandas e não está vazio
                if hasattr(pedido_data, 'empty') and not pedido_data.empty:
                    nome = str(pedido_data.get('nome', ''))
                    sobrenome = str(pedido_data.get('sobrenome', ''))
                    fone = str(pedido_data.get('fone', ''))
                elif isinstance(pedido_data, dict):
                    nome = str(pedido_data.get('nome', ''))
                    sobrenome = str(pedido_data.get('sobrenome', ''))
                    fone = str(pedido_data.get('fone', ''))
                else:
                    raise ValueError("Dados do pedido em formato inválido")
            else:
                show_message("❌ Dados do pedido não encontrados", "red")
                return
                
        except Exception as e:
            show_message(f"❌ Erro ao buscar dados do pedido: {e}", "red")
            return
        
        # Sanitiza parâmetros para URL
        try:
            params = {
                'numPedido': quote(str(num_pedido_id)),
                'idOrderPedido': quote(str(id_ordem_val)),
                'idCliente': quote(str(id_cliente_val or '')),
                'nome': quote(nome),
                'sobrenome': quote(sobrenome),
                'fone': quote(fone)
            }
            
            url = f"/produtos_todos?numPedido={params['numPedido']}&idOrderPedido={params['idOrderPedido']}&idCliente={params['idCliente']}&nome={params['nome']}&sobrenome={params['sobrenome']}&fone={params['fone']}"
            page.go(url)
            
        except Exception as e:
            show_message(f"❌ Erro ao construir URL: {e}", "red")

    # Preparação da estrutura da tabela com tratamento robusto
    colunas = ['id', 'numPedido', 'id_cliente', 'nome', 'hora']
    
    # Garante que todas as colunas existem
    if df_merged.empty:
        # Cria DataFrame vazio mas com estrutura correta
        df_merged = pd.DataFrame({col: [] for col in colunas})
    else:
        for c in colunas:
            if c not in df_merged.columns:
                df_merged[c] = ''

    columns = [ft.DataColumn(ft.Text(str(c))) for c in colunas]
    tabela_ref = ft.Ref[ft.DataTable]()

    # Sistema de filtro otimizado com debouncing
    filtro_state = {"texto": "", "last_update": 0}
    import time

    def construir_linhas():
        """Constrói linhas da tabela de forma otimizada"""
        rows_local = []
        if not df_merged.empty:
            df_filtrado = df_merged
            txt = filtro_state['texto'].strip().lower()
            
            # Aplicar filtro de forma eficiente
            if txt:
                # Usa vectorização do pandas para melhor performance
                mask = (
                    df_filtrado['nome'].astype(str).str.lower().str.contains(txt, na=False) |
                    df_filtrado['numPedido'].astype(str).str.contains(txt, na=False)
                )
                df_filtrado = df_filtrado[mask]
                
            # Constrói linhas limitando quantidade para performance
            max_rows = 100  # Limita para evitar travamento
            for idx, (_, row) in enumerate(df_filtrado.iterrows()):
                if idx >= max_rows:
                    # Avisa se há mais resultados
                    if idx == max_rows:
                        show_message(f"⚠️ Mostrando primeiros {max_rows} resultados. Use filtros para refinar.", "orange")
                    break
                    
                row_data = row.to_dict()
                row_cells = [ft.DataCell(ft.Text(str(row.get(c, "")))) for c in colunas]
                rows_local.append(ft.DataRow(
                    cells=row_cells, 
                    on_select_changed=lambda e, data=row_data: selecionar_linha(e, data)
                ))
                
        if not rows_local:
            # Linha vazia com mensagem útil
            empty_msg = "Nenhuma ordem encontrada" if filtro_state['texto'] else "Nenhum dado disponível"
            rows_local = [ft.DataRow([
                ft.DataCell(ft.Text(empty_msg)),
                *[ft.DataCell(ft.Text("")) for _ in range(len(colunas) - 1)]
            ])]
            
        return rows_local

    def aplicar_filtro_otimizado(e):
        """Aplica filtro com debouncing para melhor performance"""
        current_time = time.time()
        filtro_state['texto'] = e.control.value or ""
        filtro_state['last_update'] = current_time
        
        # Debouncing - só aplica filtro após 300ms sem digitação
        def delayed_filter():
            time.sleep(0.3)
            if time.time() - filtro_state['last_update'] >= 0.3:
                try:
                    tabela_ref.current.rows = construir_linhas()
                    page.update()
                except Exception as ex:
                    show_message(f"Erro ao aplicar filtro: {ex}", "red")
        
        import threading
        threading.Thread(target=delayed_filter, daemon=True).start()

    campo_filtro = create_filter_field("Filtrar (nome ou numPedido)", aplicar_filtro_otimizado, width=300)
    rows = construir_linhas()

    return ft.Column([
        texto_titulo("Lista de Ordens de Pedido"),
        ft.Row([
            botao_acao("Ir para Produtos Todos", on_click=ir_para_produtos_todos),
            campo_filtro,
            loading_indicator,
            msg
        ], alignment=ft.MainAxisAlignment.START, spacing=20),
        ft.Divider(),
        ft.Text("Clique em uma linha para selecionar a ordem", size=12, color="gray"),
        
        # Estatísticas úteis
        ft.Row([
            ft.Text(f"📊 Total de ordens: {len(df_merged)}", size=12, color="blue"),
            ft.Text(f"📋 Ordens com pedidos: {len(df_merged[df_merged['nome'].notna()]) if not df_merged.empty else 0}", size=12, color="green"),
        ], spacing=20) if not df_merged.empty else ft.Container(),
        
        ft.Column([
            ft.DataTable(
                ref=tabela_ref,
                columns=columns,
                rows=rows,
                expand=False,
            )
        ], spacing=1, width=1100, height=400, scroll=ft.ScrollMode.AUTO),
        
        # Rodapé com informações úteis
        ft.Container(
            ft.Row([
                ft.Text("💡 Dica: Use o filtro para encontrar ordens específicas", size=10, color="grey"),
                ft.Text("🔄 Atualize a página se não ver dados", size=10, color="grey"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10)
        ) if api_errors else ft.Container(),
    ])
