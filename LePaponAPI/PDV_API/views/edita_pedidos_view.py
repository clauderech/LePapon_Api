import flet as ft
from models.pedidostemp_api import PedidosTempAPI
from models.produtos_todos_api import ProdutosTodosAPI
from models.numpedidos_api import NumPedidosAPI
from config import BASE_URL
from views.tema_0_0_0 import texto_titulo, aplicar_tema
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class PedidoItem:
    """Classe para representar um item de pedido com validação"""
    id_cliente: str
    qtd: str
    pago: bool
    
    @classmethod
    def from_form_data(cls, id_cliente: Optional[str], qtd: Optional[str], pago: Optional[bool]):
        """Cria instância a partir de dados do formulário com validação"""
        return cls(
            id_cliente=id_cliente or "",
            qtd=qtd or "",
            pago=pago or False
        )
    
    def to_api_dict(self) -> Dict:
        return {
            'id_cliente': self.id_cliente,
            'qtd': self.qtd,
            'pago': 1 if self.pago else 0
        }

class PedidosDataManager:
    """Gerenciador centralizado para operações com dados de pedidos"""
    
    def __init__(self, base_url: str):
        self.pedidos_api = PedidosTempAPI(base_url)
        self.produtos_api = ProdutosTodosAPI(base_url)
        self.numpedidos_api = NumPedidosAPI(base_url)
        self._cache = {}
        
    def _safe_api_call(self, api_func, default_value=None):
        """Executa chamada de API com tratamento seguro de erros"""
        try:
            result = api_func()
            return result if isinstance(result, list) else ([result] if result else (default_value or []))
        except Exception as e:
            print(f"Erro na API: {e}")
            return default_value or []
    
    def get_merged_data(self, force_refresh=False):
        """Obtém dados mesclados com cache opcional"""
        if not force_refresh and 'merged_data' in self._cache:
            return self._cache['merged_data']
            
        # Carrega dados das APIs
        pedidos = self._safe_api_call(self.pedidos_api.get_all)
        produtos = self._safe_api_call(self.produtos_api.get_all)
        numpedidos = self._safe_api_call(self.numpedidos_api.get_all)
        
        # Cria mapeamento de números de pedidos
        numpedido_dict = {
            str(n.get("id")): {
                "numero": n.get("id"), 
                "nome": n.get("nome", "")
            } 
            for n in numpedidos if isinstance(n, dict)
        }
        
        # Merge dados usando pandas se disponível
        if pedidos and produtos:
            df_pedidos = pd.DataFrame(pedidos)
            df_produtos = pd.DataFrame(produtos)
            
            if not df_pedidos.empty and not df_produtos.empty:
                # Converte tipos para string para merge consistente
                df_produtos["id_Prod"] = df_produtos["id_Prod"].astype(str)
                df_pedidos["id_Prod"] = df_pedidos["id_Prod"].astype(str)
                
                df_merged = pd.merge(
                    df_pedidos, 
                    df_produtos[["id_Prod", "nome_Prod"]], 
                    on="id_Prod", 
                    how="left"
                )
                pedidos_merged = df_merged.to_dict(orient="records")
            else:
                pedidos_merged = pedidos
        else:
            pedidos_merged = pedidos
            
        # Agrupa por número de pedido
        pedidos_por_num = {}
        for p in pedidos_merged:
            num_id = str(p.get("numPedido", ""))
            info_pedido = numpedido_dict.get(num_id, {"numero": "Sem número", "nome": "Sem nome"})
            numero_real = info_pedido["numero"]
            nome_cliente = info_pedido["nome"]
            
            key = (str(numero_real), nome_cliente, num_id)
            pedidos_por_num.setdefault(key, []).append(p)
        
        # Cache resultado
        self._cache['merged_data'] = pedidos_por_num
        return pedidos_por_num
    
    def update_pedido(self, pedido_id: int, item_data: Dict, pedido_item: PedidoItem):
        """Atualiza um pedido específico"""
        novo_data = item_data.copy()
        
        # Remove campos conflitantes
        campos_remover = ["nome_Prod", "id"]
        for campo in campos_remover:
            novo_data.pop(campo, None)
            
        # Formata data se necessário
        if "data" in novo_data and novo_data["data"]:
            try:
                novo_data["data"] = pd.to_datetime(novo_data["data"]).strftime("%Y-%m-%d")
            except Exception:
                pass
                
        # Aplica novos valores
        novo_data.update(pedido_item.to_api_dict())
        
        # Atualiza via API
        return self.pedidos_api.update(pedido_id, novo_data)
    
    def delete_pedido(self, pedido_id: int):
        """Deleta um pedido específico"""
        result = self.pedidos_api.delete(pedido_id)
        # Limpa cache após mudança
        self._cache.clear()
        return result

    def invalidate_cache(self):
        """Limpa o cache forçando reload na próxima chamada"""
        self._cache.clear()

def pedidos_accordion_view(page: ft.Page):
    """Interface otimizada para edição de pedidos com accordeão"""
    
    # Inicialização
    data_manager = PedidosDataManager(BASE_URL)
    msg = ft.Text(visible=False)
    aplicar_tema(page)
    page.title = "Editar Pedidos - Lanchonete"
    
    def show_message(text: str, color: str = "green"):
        """Helper para exibir mensagens de status"""
        msg.value = text
        msg.color = color
        msg.visible = True
        page.update()
    
    def handle_delete(pedido_id: Optional[int]):
        """Handler otimizado para deletar pedido"""
        def delete_action(e):
            if pedido_id is None:
                show_message("ID do pedido inválido!", "red")
                return
            try:
                data_manager.delete_pedido(pedido_id)
                show_message("Pedido deletado com sucesso!", "green")
                atualizar_tabela()
            except Exception as ex:
                show_message(f"Erro ao deletar: {ex}", "red")
        return delete_action
    
    def handle_update(pedido_id: Optional[int], item_data: Dict, campo_cliente: ft.TextField, 
                     campo_qtd: ft.TextField, campo_pago: ft.Checkbox):
        """Handler otimizado para atualizar pedido"""
        def update_action(e):
            if pedido_id is None:
                show_message("ID do pedido inválido!", "red")
                return
            try:
                # Validação básica
                if not campo_qtd.value or not campo_qtd.value.strip():
                    show_message("Quantidade não pode estar vazia!", "red")
                    return
                    
                pedido_item = PedidoItem.from_form_data(
                    id_cliente=campo_cliente.value,
                    qtd=campo_qtd.value,
                    pago=campo_pago.value
                )
                
                data_manager.update_pedido(pedido_id, item_data, pedido_item)
                show_message("Pedido atualizado com sucesso!", "green")
                atualizar_tabela()
                
            except Exception as ex:
                show_message(f"Erro ao atualizar: {ex}", "red")
        return update_action
    
    def criar_linha_item(item: Dict) -> ft.Row:
        """Cria uma linha de item otimizada com campos editáveis"""
        id_pedido = item.get("id")
        # Converte para int se possível, senão None
        try:
            id_pedido_int = int(id_pedido) if id_pedido is not None else None
        except (ValueError, TypeError):
            id_pedido_int = None
            
        id_prod = str(item.get("id_Prod", ""))
        id_cliente = str(item.get("id_cliente", ""))
        nome_prod = str(item.get("nome_Prod", ""))
        qtd = str(item.get("qtd", ""))
        v_unit = str(item.get("V_unit", ""))
        pago = bool(item.get("pago", False))
        
        # Campos editáveis
        campo_id_cliente = ft.TextField(
            value=id_cliente, 
            label="ID Cliente", 
            width=100, 
            height=40
        )
        campo_qtd = ft.TextField(
            value=qtd, 
            label="Quantidade", 
            width=100, 
            height=40
        )
        campo_pago = ft.Checkbox(value=pago, label="Pago")
        
        return ft.Row([
            ft.TextField(value=id_prod, label="ID Produto", width=130, height=40, read_only=True),
            campo_id_cliente,
            ft.TextField(value=nome_prod, label="Produto", width=300, height=40, read_only=True),
            campo_qtd,
            ft.TextField(value=v_unit, label="Valor Unitário", width=130, height=40, read_only=True),
            campo_pago,
            ft.IconButton(
                icon=ft.Icons.DELETE, 
                tooltip="Deletar", 
                on_click=handle_delete(id_pedido_int),
                disabled=id_pedido_int is None
            ),
            ft.IconButton(
                icon=ft.Icons.SAVE, 
                tooltip="Atualizar", 
                on_click=handle_update(id_pedido_int, item, campo_id_cliente, campo_qtd, campo_pago),
                disabled=id_pedido_int is None
            ),
        ], height=50, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=5)

    def atualizar_tabela(force_refresh: bool = True):
        """Atualiza a tabela com dados otimizados e cache"""
        try:
            pedidos_por_num = data_manager.get_merged_data(force_refresh)
            
            panels = []
            for (numero_real, nome_cliente, num_id), lista in pedidos_por_num.items():
                # Cria linhas de itens de forma otimizada
                detalhes = [criar_linha_item(item) for item in lista]
                
                panels.append(
                    ft.ExpansionPanel(
                        header=ft.Text(f"Pedido {numero_real} | ID: {num_id} | Cliente: {nome_cliente}"),
                        content=ft.Column(detalhes),                    
                    )
                )
            
            accordion.controls = panels
            page.update()
            
        except Exception as ex:
            show_message(f"Erro ao carregar dados: {ex}", "red")
    
    def coletar_todos_valores():
        """Coleta valores de todos os campos de texto e checkbox na interface"""
        valores_coletados = []
        
        # Percorre todos os panels do accordion
        for panel in accordion.controls:
            if isinstance(panel, ft.ExpansionPanel):
                # Pega o header para identificar o pedido  
                header_text = "Pedido desconhecido"
                try:
                    if hasattr(panel, 'header') and hasattr(panel.header, 'value'):
                        header_text = getattr(panel.header, 'value', 'Pedido sem ID')
                except:
                    pass
                
                # Percorre o conteúdo do panel
                if hasattr(panel, 'content') and isinstance(panel.content, ft.Column):
                    for row in panel.content.controls:
                        if isinstance(row, ft.Row):
                            # Extrai valores dos campos editáveis na linha
                            valores_linha = {
                                'pedido_header': header_text,
                                'id_produto': None,
                                'id_cliente': None,
                                'nome_produto': None,
                                'quantidade': None,
                                'valor_unitario': None,
                                'pago': None
                            }
                            
                            # Percorre os controles da linha
                            for i, control in enumerate(row.controls):
                                if isinstance(control, ft.TextField):
                                    if i == 0:  # ID Produto (read-only)
                                        valores_linha['id_produto'] = control.value
                                    elif i == 1:  # ID Cliente (editável)
                                        valores_linha['id_cliente'] = control.value
                                    elif i == 2:  # Nome Produto (read-only)
                                        valores_linha['nome_produto'] = control.value
                                    elif i == 3:  # Quantidade (editável)
                                        valores_linha['quantidade'] = control.value
                                    elif i == 4:  # Valor Unitário (read-only)
                                        valores_linha['valor_unitario'] = control.value
                                elif isinstance(control, ft.Checkbox):
                                    valores_linha['pago'] = control.value
                            
                            # Adiciona à lista se tiver dados válidos
                            if valores_linha['id_produto'] is not None:
                                valores_coletados.append(valores_linha)
        
        return valores_coletados
    
    def mostrar_valores_coletados(e):
        """Demonstra como coletar e exibir os valores"""
        valores = coletar_todos_valores()
        
        # Exibe os valores coletados
        print("=== VALORES COLETADOS ===")
        for i, item in enumerate(valores):
            print(f"Item {i+1}:")
            print(f"  Pedido: {item['pedido_header']}")
            print(f"  ID Produto: {item['id_produto']}")
            print(f"  ID Cliente: {item['id_cliente']}")
            print(f"  Nome Produto: {item['nome_produto']}")
            print(f"  Quantidade: {item['quantidade']}")
            print(f"  Valor Unitário: {item['valor_unitario']}")
            print(f"  Pago: {item['pago']}")
            print("-" * 40)
        
        # Mostra mensagem na interface
        show_message(f"Coletados {len(valores)} itens. Veja o console para detalhes.", "blue")
    
    def enviar_dados_coletados(e):
        """Coleta todos os valores e envia para o banco de dados"""
        try:
            # Coleta os valores atuais da interface
            valores = coletar_todos_valores()
            
            if not valores:
                show_message("Nenhum dado encontrado para enviar!", "orange")
                return
            
            # Contadores para feedback
            sucessos = 0
            erros = 0
            erros_detalhes = []
            
            show_message(f"Enviando {len(valores)} itens para o banco...", "blue")
            
            # Processa cada item coletado
            for item in valores:
                try:
                    # Extrai o ID do pedido do produto (precisa estar nos dados originais)
                    # Vamos buscar pelos dados originais para pegar o ID do registro
                    pedidos_por_num = data_manager.get_merged_data(force_refresh=False)
                    
                    pedido_id = None
                    # Procura o ID do pedido pelos dados originais
                    for (numero_real, nome_cliente, num_id), lista in pedidos_por_num.items():
                        for pedido_original in lista:
                            # Compara pelos campos únicos para encontrar o registro correto
                            if (str(pedido_original.get("id_Prod", "")) == str(item['id_produto']) and
                                str(pedido_original.get("nome_Prod", "")) == str(item['nome_produto'])):
                                pedido_id = pedido_original.get("id")
                                break
                        if pedido_id:
                            break
                    
                    if pedido_id is None:
                        erros += 1
                        erros_detalhes.append(f"ID não encontrado para produto {item['id_produto']}")
                        continue
                    
                    # Converte para int
                    pedido_id_int = int(pedido_id)
                    
                    # Prepara os dados para update
                    dados_update = {
                        'id_cliente': item['id_cliente'] or "",
                        'qtd': item['quantidade'] or "0",
                        'pago': 1 if item['pago'] else 0
                    }
                    
                    # Busca os dados originais para manter outros campos
                    for (numero_real, nome_cliente, num_id), lista in pedidos_por_num.items():
                        for pedido_original in lista:
                            if pedido_original.get("id") == pedido_id:
                                # Copia dados originais e aplica as alterações
                                novo_data = pedido_original.copy()
                                
                                # Remove campos conflitantes
                                campos_remover = ["nome_Prod", "id"]
                                for campo in campos_remover:
                                    novo_data.pop(campo, None)
                                
                                # Aplica as alterações
                                novo_data.update(dados_update)
                                
                                # Formata data se necessário
                                if "data" in novo_data and novo_data["data"]:
                                    try:
                                        novo_data["data"] = pd.to_datetime(novo_data["data"]).strftime("%Y-%m-%d")
                                    except Exception:
                                        pass
                                
                                # Envia para a API
                                resultado = data_manager.pedidos_api.update(pedido_id_int, novo_data)
                                sucessos += 1
                                break
                    
                except Exception as ex:
                    erros += 1
                    erros_detalhes.append(f"Erro no item {item['id_produto']}: {str(ex)}")
                    print(f"Erro ao processar item {item['id_produto']}: {ex}")
            
            # Limpa cache após mudanças
            data_manager.invalidate_cache()
            
            # Exibe resultado
            if erros == 0:
                show_message(f"✅ Todos os {sucessos} itens enviados com sucesso!", "green")
            else:
                show_message(f"⚠️ {sucessos} sucessos, {erros} erros. Veja console para detalhes.", "orange")
                print("=== ERROS DETALHADOS ===")
                for erro in erros_detalhes:
                    print(f"- {erro}")
            
            # Atualiza a interface
            if campo_num_pedido.value and campo_num_pedido.value.strip():
                # Se há filtro ativo, reaplica
                filtrar_por_pedido(None)
            else:
                # Senão, atualiza tudo
                atualizar_tabela(force_refresh=True)
                
        except Exception as ex:
            show_message(f"Erro ao enviar dados: {ex}", "red")
            print(f"Erro geral ao enviar dados: {ex}")
    
    def refresh_data(e):
        """Força refresh dos dados limpando cache"""
        data_manager.invalidate_cache()
        atualizar_tabela(force_refresh=True)
        show_message("Dados atualizados!", "green")

    # Inicialização da interface
    accordion = ft.ExpansionPanelList(controls=[], expand=True, spacing=10)
    
    # Campo para filtrar por número do pedido
    campo_num_pedido = ft.TextField(
        label="Número do Pedido",
        hint_text="Digite o número do pedido para filtrar",
        width=200,
        height=40
    )
    
    def filtrar_por_pedido(e):
        """Filtra e exibe apenas o pedido com o número especificado"""
        numero_digitado = campo_num_pedido.value
        if not numero_digitado or not numero_digitado.strip():
            show_message("Digite um número de pedido para filtrar!", "orange")
            return
            
        try:
            pedidos_por_num = data_manager.get_merged_data(force_refresh=False)
            panels = []
            
            # Procura pelo número digitado
            encontrou = False
            for (numero_real, nome_cliente, num_id), lista in pedidos_por_num.items():
                # Verifica se o número digitado corresponde
                if str(numero_real) == numero_digitado.strip() or str(num_id) == numero_digitado.strip():
                    encontrou = True
                    # Cria linhas de itens de forma otimizada
                    detalhes = [criar_linha_item(item) for item in lista]
                    
                    panels.append(
                        ft.ExpansionPanel(
                            header=ft.Text(f"Pedido {numero_real} | ID: {num_id} | Cliente: {nome_cliente}"),
                            content=ft.Column(detalhes)
                        )
                    )
            
            if encontrou:
                accordion.controls = panels
                show_message(f"Pedido {numero_digitado} encontrado!", "green")
            else:
                accordion.controls = []
                show_message(f"Pedido {numero_digitado} não encontrado!", "red")
                
            page.update()
            
        except Exception as ex:
            show_message(f"Erro ao filtrar pedido: {ex}", "red")
    
    # Botão para filtrar pedido
    btn_filtrar = ft.ElevatedButton(
        text="Filtrar Pedido",
        icon=ft.Icons.SEARCH,
        on_click=filtrar_por_pedido,
        tooltip="Filtra pelo número do pedido digitado",
        color="green"
    )
    
    # Botão para limpar filtro
    def limpar_filtro(e):
        """Remove o filtro e mostra todos os pedidos"""
        campo_num_pedido.value = ""
        atualizar_tabela(force_refresh=False)
        show_message("Filtro removido - mostrando todos os pedidos", "blue")
        page.update()
    
    btn_limpar = ft.ElevatedButton(
        text="Mostrar Todos",
        icon=ft.Icons.CLEAR,
        on_click=limpar_filtro,
        tooltip="Remove o filtro e mostra todos os pedidos"
    )
    
    # Botão de refresh
    btn_refresh = ft.ElevatedButton(
        text="Atualizar Dados",
        icon=ft.Icons.REFRESH,
        on_click=refresh_data,
        tooltip="Recarregar dados do servidor"
    )
    
    # Botão para demonstrar coleta de valores
    btn_coletar = ft.ElevatedButton(
        text="Coletar Valores",
        icon=ft.Icons.COLLECTIONS,
        on_click=mostrar_valores_coletados,
        tooltip="Demonstra como coletar valores dos campos",
        color="orange"
    )
    
    # Botão para enviar dados para o banco
    btn_enviar = ft.ElevatedButton(
        text="Enviar para DB",
        icon=ft.Icons.SEND,
        on_click=enviar_dados_coletados,
        tooltip="Coleta todos os valores editados e envia para o banco de dados",
        color="red"
    )
    
    # Carrega dados iniciais
    atualizar_tabela()
    
    return ft.Column([
        texto_titulo("Pedidos agrupados por número"),
        # Seção de filtros
        ft.Container(
            content=ft.Row([
                campo_num_pedido,
                btn_filtrar,
                btn_limpar
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            bgcolor="#f0f0f0",
            border_radius=5,
            padding=10
        ),
        # Seção de ações
        ft.Row([btn_refresh, btn_coletar, btn_enviar], alignment=ft.MainAxisAlignment.END, spacing=10),
        msg,
        ft.Column([accordion],
            scroll=ft.ScrollMode.ALWAYS, 
            width=1100, 
            height=500  # Reduzido um pouco para dar espaço aos filtros
        ) 
    ])