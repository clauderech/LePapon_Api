import flet as ft
import os
import datetime
import re
import requests
from pathlib import Path
from contextlib import contextmanager
from models.pedidostemp_api import PedidosTempAPI
from models.numpedidos_api import NumPedidosAPI
from models.produtos_todos_api import ProdutosTodosAPI
from models.enviar_relatorio_pedido import EnviarRelatorioPedido
from views.tema_0_0_0 import texto_titulo, aplicar_tema, texto_padrao, botao_acao
import pandas as pd
from config import BASE_URL
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import paramiko

# Carrega variáveis de ambiente
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../.env'))

pedidostemp_api = PedidosTempAPI(BASE_URL)
numpedidos_api = NumPedidosAPI(BASE_URL)
produtos_todos_api = ProdutosTodosAPI(BASE_URL)

def pedidostemp_view(page: ft.Page):
    print('[DEBUG] pedidostemp_view construída (entrada)')

    # Cache simples para dados da API
    _api_cache = {}

    def get_cached_data(api_func, cache_key):
        """Cache simples para evitar múltiplas chamadas API"""
        if cache_key not in _api_cache:
            try:
                data = api_func()
                _api_cache[cache_key] = data
            except Exception as e:
                print(f"[ERROR] Erro ao buscar {cache_key}: {e}")
                _api_cache[cache_key] = []
        
        return _api_cache[cache_key]

    msg_pdf = ft.Text(value="", color="green", visible=False)
    estado_pdf: dict[str, str] = {"pdf_path": "", "telefone": "", "url_remota": ""}

    def normalizar_fone(fone: str) -> str:
        """Normaliza número de telefone de forma segura"""
        if not fone:
            return ""
        digits = re.sub(r"\D", "", fone)
        # Garante DDI 55
        if digits.startswith('0'):
            digits = digits.lstrip('0')
        if not digits.startswith('55') and len(digits) >= 10:
            digits = '55' + digits
        return digits

    def sanitize_filename(filename: str) -> str:
        """Sanitiza nome de arquivo para evitar path injection"""
        if not filename:
            return "pedido_invalido"
        # Remove caracteres perigosos
        sanitized = re.sub(r'[<>:"/\\|?*\.\.]', '', str(filename))
        # Limita tamanho
        return sanitized[:50] if sanitized else "pedido_invalido"

    def safe_float_convert(value, default=0.0):
        """Converte valor para float de forma segura"""
        if value is None:
            return default
        try:
            if isinstance(value, (int, float)):
                return float(value)
            # Trata string com vírgula decimal brasileira
            str_val = str(value).strip().replace(',', '.')
            return float(str_val) if str_val else default
        except (ValueError, TypeError) as e:
            print(f"[WARN] Erro na conversão float: {value} -> {e}")
            return default

    def gerar_pdf_pedido(e=None, apenas_gerar: bool = True):
        """Gera o PDF local do pedido selecionado. Se apenas_gerar=False, também retorna metadados."""
        num_pedido_sel = selected_num_pedido.current.value
        msg_pdf.value = ""
        msg_pdf.visible = False
        page.update()
        
        if not num_pedido_sel:
            msg_pdf.value = "Selecione um número de pedido para gerar o PDF."
            msg_pdf.color = "red"
            msg_pdf.visible = True
            page.update()
            return None
            
        # Sanitiza o número do pedido
        num_pedido_sanitized = sanitize_filename(str(num_pedido_sel))
        
        try:
            data = pedidostemp_api.get_all()
            if not isinstance(data, list):
                data = [data] if data else []
            pedidos_filtrados = [d for d in data if str(d.get('numPedido', '')) == str(num_pedido_sel)]
            
            produtos = produtos_todos_api.get_all()
            if not isinstance(produtos, list):
                produtos = [produtos] if produtos else []
                
            # Buscar dados do cliente em numpedidos
            cliente_nome = cliente_sobrenome = cliente_telefone = cliente_endereco = ""
            try:
                numpedido = numpedidos_api.get_by_id(num_pedido_sel)
                if isinstance(numpedido, dict):
                    cliente_nome = numpedido.get('nome', '')
                    cliente_sobrenome = numpedido.get('sobrenome', '')
                    cliente_telefone = numpedido.get('fone', '')
                    cliente_endereco = numpedido.get('endereco', '')
            except (requests.RequestException, KeyError, AttributeError) as e:
                print(f"[WARN] Erro ao buscar dados do cliente: {e}")
                
            df_pedidos = pd.DataFrame(pedidos_filtrados)
            df_produtos = pd.DataFrame(produtos)
            
            if not df_pedidos.empty and not df_produtos.empty:
                df_merged = pd.merge(
                    df_pedidos,
                    df_produtos[['id_Prod', 'nome_Prod', 'Valor_Prod']],
                    left_on='id_Prod', right_on='id_Prod', how='left', suffixes=('', '_Prod')
                )
            else:
                df_merged = df_pedidos
                
            if 'qtd' in df_merged.columns and 'Valor_Prod' in df_merged.columns:
                df_merged['sub_total'] = df_merged.apply(
                    lambda row: safe_float_convert(row['qtd']) * safe_float_convert(row['Valor_Prod']), 
                    axis=1
                )
            else:
                df_merged['sub_total'] = 0.0
                
            data_pdf = datetime.datetime.now().strftime('%Y-%m-%d')
            pasta_destino = os.path.join(os.path.dirname(__file__), f'../PedidosPDF/{data_pdf}')
            
            # Verifica se pode criar diretório
            try:
                os.makedirs(pasta_destino, exist_ok=True)
            except (OSError, PermissionError) as e:
                msg_pdf.value = f"Erro ao criar diretório: {e}"
                msg_pdf.color = "red"
                msg_pdf.visible = True
                page.update()
                return None
                
            pdf_path = os.path.join(pasta_destino, f'pedido_{num_pedido_sanitized}.pdf')
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../acents/L.png'))
            try:
                c.drawImage(logo_path, 40, height-100, width=60, height=60, preserveAspectRatio=True, mask='auto')
            except Exception:
                c.setFont("Helvetica", 8)
                c.drawString(40, height-100, f"[Logo não encontrado]")
            c.setFont("Helvetica-Bold", 16)
            c.drawString(110, height-60, "LePapon Lanches - Claudemir")
            c.setFont("Helvetica", 10)
            c.drawString(110, height-80, "Endereço: João Venâncio Girarde, nº 260")
            c.drawString(110, height-95, "CNPJ: 33.794.253/0001-33   Fone: (55) 5499-2635135")
            c.setFont("Helvetica", 10)
            c.drawString(400, height-60, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, height-120, f"Pedido Nº: {num_pedido_sel}")
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, height-140, f"Cliente: {cliente_nome} {cliente_sobrenome}")
            c.setFont("Helvetica", 10)
            c.drawString(40, height-155, f"Telefone: {cliente_telefone}")
            c.drawString(250, height-155, f"Endereço: {cliente_endereco}")
            y = height-175
            colunas_legenda = ['Qtd', 'Produto', 'Valor Unit.', 'Subtotal']
            col_widths = [50, 200, 70, 70]
            x_positions = [40]
            for w in col_widths[:-1]:
                x_positions.append(x_positions[-1] + w)
            for i, campo in enumerate(colunas_legenda):
                c.drawString(x_positions[i], y, campo)
            y -= 20
            total = 0.0
            for _, row in df_merged.iterrows():
                c.drawString(x_positions[0], y, str(row.get('qtd', '')))
                c.drawString(x_positions[1], y, str(row.get('nome_Prod', '')))
                c.drawString(x_positions[2], y, str(row.get('Valor_Prod', '')))
                c.drawString(x_positions[3], y, f"{row.get('sub_total', 0):.2f}")
                try:
                    total += safe_float_convert(row.get('sub_total', 0))
                except Exception as e:
                    print(f"[WARN] Erro ao somar total: {e}")
                y -= 18
                if y < 60:
                    c.showPage()
                    y = height-40
            if y < 80:
                c.showPage()
                y = height-40
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y-10, f"Total do pedido: R$ {total:.2f}")
            c.save()
            estado_pdf['pdf_path'] = pdf_path or ""
            # Usa telefone do cliente ou padrão do ambiente
            telefone_cliente = normalizar_fone(cliente_telefone)
            telefone_padrao = os.getenv('TELEFONE_PADRAO', '555491253180')
            estado_pdf['telefone'] = telefone_cliente if telefone_cliente else normalizar_fone(telefone_padrao)
            msg_pdf.value = f"PDF gerado em: {pdf_path}"
            msg_pdf.color = "green"
            msg_pdf.visible = True
            page.update()
            print(f"[DEBUG] PDF gerado: {pdf_path}")
            return pdf_path
        except Exception as ex:
            msg_pdf.value = f"Erro ao gerar PDF: {ex}"
            msg_pdf.color = "red"
            msg_pdf.visible = True
            page.update()
            return None

    @contextmanager
    def ssh_connection(host, usuario, caminho_chave):
        """Context manager para conexões SSH/SFTP seguras"""
        transport = None
        sftp = None
        try:
            key = paramiko.RSAKey.from_private_key_file(caminho_chave)
            transport = paramiko.Transport((host, 22))
            transport.connect(username=usuario, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            yield sftp
        except (paramiko.SSHException, FileNotFoundError, OSError) as e:
            print(f"[ERROR] Erro na conexão SSH: {e}")
            raise
        finally:
            if sftp:
                try:
                    sftp.close()
                except Exception as e:
                    print(f"[WARN] Erro ao fechar SFTP: {e}")
            if transport:
                try:
                    transport.close()
                except Exception as e:
                    print(f"[WARN] Erro ao fechar Transport: {e}")

    def criar_diretorios_remotos(sftp, pasta_remota):
        """Cria diretórios remotos de forma segura"""
        try:
            partes = pasta_remota.strip('/').split('/')
            caminho_acum = ''
            for p in partes:
                if not p:  # Evita partes vazias
                    continue
                caminho_acum += '/' + p
                try:
                    sftp.stat(caminho_acum)
                except IOError:
                    try:
                        sftp.mkdir(caminho_acum)
                        print(f"[DEBUG] Diretório remoto criado: {caminho_acum}")
                    except (OSError, paramiko.SFTPError) as de:
                        print(f"[WARN] Falha ao criar dir {caminho_acum}: {de}")
        except Exception as e:
            print(f"[WARN] Erro geral na criação de diretórios: {e}")

    # Botão 1: exportar (gera + upload)
    GRAPH_API_TOKEN = os.getenv('GRAPH_API_TOKEN', '') or ''
    PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_ID', '465787769946848') or '465787769946848'
    
    # Validação de variáveis críticas
    if not GRAPH_API_TOKEN:
        print('[WARN] GRAPH_API_TOKEN não definido - funcionalidade WhatsApp limitada')
        
    def exportar_pdf_servidor(e):
        print('[DEBUG] exportar_pdf_servidor acionada')
        pdf_path = gerar_pdf_pedido()
        if not pdf_path:
            print('[DEBUG] Abortado: geração de PDF falhou')
            return
        if not os.path.isfile(pdf_path):
            msg_pdf.value = f'Arquivo PDF não encontrado: {pdf_path}'
            msg_pdf.color = 'red'
            msg_pdf.visible = True
            page.update()
            print(f'[DEBUG] Arquivo inexistente após gerar: {pdf_path}')
            return
        # Upload não depende do token WhatsApp; apenas o envio posterior.
        if not GRAPH_API_TOKEN:
            print('[WARN] GRAPH_API_TOKEN ausente - upload prossegue, envio via WhatsApp depois falhará até definir token.')
        try:
            uploader = EnviarRelatorioPedido(token=str(GRAPH_API_TOKEN or ''), phone_number_id=str(PHONE_NUMBER_ID))
            host = os.getenv('DROPLET_HOST', '64.23.179.108')
            usuario = os.getenv('DROPLET_USER', 'claus')
            caminho_chave = os.path.expanduser(os.getenv('DROPLET_KEY_PATH', '~/.ssh/id_rsa'))
            nome_remoto = os.path.basename(pdf_path)
            pasta_remota = "/var/www/lepapon.com.br/Android-LePapon-Pedidos/files/pedidos_relatorios"
            caminho_remoto = f"{pasta_remota}/{nome_remoto}"
            
            print(f"[DEBUG] Preparando upload: host={host}, usuario={usuario}, caminho_remoto={caminho_remoto}")
            
            # Cria diretório remoto usando context manager
            try:
                with ssh_connection(host, usuario, caminho_chave) as sftp:
                    criar_diretorios_remotos(sftp, pasta_remota)
            except Exception as de:
                print(f"[WARN] Não foi possível garantir criação de diretórios remotos: {de}")

            print(f"[DEBUG] Iniciando upload do PDF para o servidor: {caminho_remoto}")
            uploader.upload_pdf_droplet(host, usuario, pdf_path, caminho_remoto, caminho_chave)
            
            # Validar tamanho remoto usando context manager
            try:
                with ssh_connection(host, usuario, caminho_chave) as sftp:
                    if sftp:  # Verifica se conexão foi bem-sucedida
                        statinfo = sftp.stat(caminho_remoto)
                        tamanho_remoto = statinfo.st_size
                        tamanho_local = os.path.getsize(pdf_path)
                        print(f"[DEBUG] Upload verificado. Local={tamanho_local} bytes, Remoto={tamanho_remoto} bytes")
                        
                        if tamanho_local != tamanho_remoto:
                            raise Exception(f"Tamanhos diferentes! Local: {tamanho_local}, Remoto: {tamanho_remoto}")
            except Exception as ve:
                print(f"[WARN] Não foi possível validar upload: {ve}")

            url_publica = f"https://lepapon.com.br/api/relatorios/pedidos/{nome_remoto}"
            estado_pdf['url_remota'] = url_publica or ""
            msg_pdf.value = f"Exportado para servidor: {url_publica}"
            msg_pdf.color = 'green'
            msg_pdf.visible = True
            page.update()
            print('[DEBUG] Exportação concluída com sucesso')
        except Exception as ex:
            msg_pdf.value = f"Erro ao exportar: {ex}"
            msg_pdf.color = 'red'
            msg_pdf.visible = True
            page.update()
            print(f"[ERRO exportar] {ex}")

    # Botão 2: enviar para cliente (WhatsApp)
    def enviar_pdf_cliente(e):
        print("[DEBUG] Clique no botão Enviar ao Cliente")
        if not estado_pdf.get('url_remota'):
            msg_pdf.value = 'Exporte primeiro para o servidor.'
            msg_pdf.color = 'red'
            msg_pdf.visible = True
            print('[DEBUG] Falha: exporte primeiro para o servidor.')
            page.update()
            return
        telefone = normalizar_fone(estado_pdf.get('telefone') or "")
        if not telefone:
            msg_pdf.value = 'Telefone do cliente não encontrado.'
            msg_pdf.color = 'red'
            msg_pdf.visible = True
            print('[DEBUG] Telefone ausente')
            page.update()
            return
        if not GRAPH_API_TOKEN:
            msg_pdf.value = 'Token WhatsApp ausente.'
            msg_pdf.color = 'red'
            msg_pdf.visible = True
            print('[DEBUG] Token ausente')
            page.update()
            return
        try:
            uploader = EnviarRelatorioPedido(token=str(GRAPH_API_TOKEN), phone_number_id=str(PHONE_NUMBER_ID))
            resposta = uploader.enviar_pdf(numero_cliente=str(telefone), pdf_url=str(estado_pdf['url_remota']))
            if isinstance(resposta, dict) and resposta.get('messages'):
                msg_pdf.value = f"Enviado ao cliente ({telefone})."
                msg_pdf.color = 'green'
            else:
                msg_pdf.value = f"Tentativa de envio realizada. Resposta: {resposta}"
                msg_pdf.color = 'orange'
            msg_pdf.visible = True
            print('[DEBUG] Envio processado')
            page.update()
        except Exception as ex:
            msg_pdf.value = f'Erro ao enviar: {ex}'
            msg_pdf.color = 'red'
            msg_pdf.visible = True
            print(f"[ERRO envio] {ex}")
            print('[DEBUG] Erro no envio')
            page.update()

    selected_num_pedido = ft.Ref[ft.Dropdown]()
    tabela = ft.Ref[ft.DataTable]()
    aplicar_tema(page)
    page.title = "Pedidos Temporários - Lanchonete"

    try:
        nums = get_cached_data(numpedidos_api.get_all, 'numpedidos')
        if not isinstance(nums, list):
            nums = [nums] if nums else []
    except Exception as e:
        print(f"[ERROR] Erro ao carregar números de pedidos: {e}")
        nums = []
        
    opcoes_numpedidos = [
        ft.dropdown.Option(text=f"{n.get('id', '')} - {n.get('nome', '')} - {n.get('sobrenome', '')}", key=str(n.get('id', ''))) 
        for n in nums if isinstance(n, dict) and n.get('id')
    ]

    def validate_pedido_data(data):
        """Valida estrutura dos dados de pedidos"""
        if not isinstance(data, list):
            data = [data] if data else []
        
        valid_pedidos = []
        for pedido in data:
            if not isinstance(pedido, dict):
                continue
            # Valida campos obrigatórios
            if all(key in pedido for key in ['id', 'numPedido']):
                valid_pedidos.append(pedido)
        return valid_pedidos

    def validate_produto_data(data):
        """Valida estrutura dos dados de produtos"""
        if not isinstance(data, list):
            data = [data] if data else []
        
        valid_produtos = []
        for produto in data:
            if not isinstance(produto, dict):
                continue
            # Valida campos obrigatórios
            if all(key in produto for key in ['id_Prod', 'nome_Prod']):
                valid_produtos.append(produto)
        return valid_produtos

    def atualizar_status(row_id, field, value):
        """Atualiza status de um pedido específico com validação"""
        if not row_id or not field:
            print(f"[ERROR] Parâmetros inválidos: row_id={row_id}, field={field}")
            return
            
        # Valida o valor para campos booleanos/numéricos
        if field == "pago" and value not in [0, 1]:
            print(f"[ERROR] Valor inválido para campo 'pago': {value}")
            return
            
        print(f"atualizar_status chamado: row_id={row_id}, field={field}, value={value}")
        try:
            pedido = pedidostemp_api.get_by_id(row_id)
            if not isinstance(pedido, dict):
                print(f"[ERROR] Pedido não encontrado ou dados inválidos: {row_id}")
                return
            
            if not pedido:  # Verifica se o dict está vazio
                print(f"[ERROR] Pedido vazio para ID: {row_id}")
                return
                
            pedido[field] = value
            
            # Valida e formata data se presente
            if 'data' in pedido and pedido['data']:
                try:
                    pedido['data'] = pd.to_datetime(pedido['data']).strftime('%Y-%m-%d')
                except (ValueError, TypeError) as e:
                    print(f"[WARN] Erro ao formatar data: {e}")
                    
            res_status = pedidostemp_api.update(row_id, pedido)
            print(f"Status atualizado: {res_status}")
            
            # Limpa cache e atualiza UI apenas se a atualização foi bem-sucedida
            if 'pedidos' in _api_cache:
                del _api_cache['pedidos']
            
            # Agenda atualização da UI para evitar conflitos
            page.update()
            filtrar_pedidos()
            
        except (requests.RequestException, KeyError, AttributeError) as e:
            print(f"Erro ao atualizar status: {e}")
        except Exception as e:
            print(f"Erro geral ao atualizar status: {e}")
    
    def marcar_todos_pagos(e=None):
        """Marca todos os itens do pedido selecionado como pagos"""
        num_pedido_sel = selected_num_pedido.current.value
        if not num_pedido_sel:
            msg_pdf.value = "Selecione um número de pedido primeiro!"
            msg_pdf.color = "red"
            msg_pdf.visible = True
            page.update()
            return
        
        try:
            # Usa cache para buscar pedidos
            data = get_cached_data(pedidostemp_api.get_all, 'pedidos')
            data = validate_pedido_data(data)
            
            # Filtra pelos itens do pedido selecionado
            pedidos_filtrados = [d for d in data if str(d.get('numPedido', '')) == str(num_pedido_sel)]
            
            if not pedidos_filtrados:
                msg_pdf.value = f"Nenhum item encontrado para o pedido {num_pedido_sel}!"
                msg_pdf.color = "orange"
                msg_pdf.visible = True
                page.update()
                return
            
            # Contador para feedback
            sucessos = 0
            erros = 0
            
            # Atualiza cada item para pago = 1
            for pedido in pedidos_filtrados:
                pedido_id = pedido.get('id')
                if pedido_id:
                    try:
                        # Busca o pedido individual para update
                        pedido_individual = pedidostemp_api.get_by_id(pedido_id)
                        if isinstance(pedido_individual, dict):
                            pedido_individual['pago'] = 1
                            
                            # Formata data se necessário
                            if 'data' in pedido_individual and pedido_individual['data']:
                                try:
                                    pedido_individual['data'] = pd.to_datetime(pedido_individual['data']).strftime('%Y-%m-%d')
                                except (ValueError, TypeError) as e:
                                    print(f"[WARN] Erro ao formatar data: {e}")
                            
                            # Atualiza via API
                            pedidostemp_api.update(pedido_id, pedido_individual)
                            sucessos += 1
                    except (requests.RequestException, KeyError, AttributeError) as ex:
                        print(f"Erro ao atualizar item {pedido_id}: {ex}")
                        erros += 1
            
            # Limpa cache para forçar refresh
            if 'pedidos' in _api_cache:
                del _api_cache['pedidos']
                
            # Atualiza a tabela
            filtrar_pedidos()
            
            # Feedback para o usuário
            if erros == 0:
                msg_pdf.value = f"✅ Todos os {sucessos} itens do pedido {num_pedido_sel} marcados como pagos!"
                msg_pdf.color = "green"
            else:
                msg_pdf.value = f"⚠️ {sucessos} sucessos, {erros} erros ao marcar como pagos"
                msg_pdf.color = "orange"
            
            msg_pdf.visible = True
            page.update()
            
        except Exception as ex:
            msg_pdf.value = f"Erro ao marcar todos como pagos: {ex}"
            msg_pdf.color = "red" 
            msg_pdf.visible = True
            page.update()
            print(f"Erro geral ao marcar todos como pagos: {ex}")

    totais_nao_pagos = ft.TextField(label="Total Não Pago", value="0.00", read_only=True, width=150)
    totais_pagos = ft.TextField(label="Total Pago", value="0.00", read_only=True, width=150)
    saldo_devedor = ft.TextField(label="Saldo Devedor", value="0.00", read_only=True, width=150)

    def filtrar_pedidos(e=None):
        """Filtra e exibe pedidos com cache e validação melhorada"""
        num_pedido_sel = selected_num_pedido.current.value
        
        # Usa cache para dados da API
        try:
            data = get_cached_data(pedidostemp_api.get_all, 'pedidos')
            data = validate_pedido_data(data)
        except Exception as e:
            print(f"[ERROR] Erro ao carregar pedidos: {e}")
            data = []
            
        pedidos_filtrados = [d for d in data if str(d.get('numPedido', '')) == str(num_pedido_sel)] if num_pedido_sel else []
        print(f"[DEBUG] Pedidos filtrados para {num_pedido_sel}: {len(pedidos_filtrados)} itens encontrados")
        # Usa cache para produtos
        try:
            produtos = get_cached_data(produtos_todos_api.get_all, 'produtos')
            produtos = validate_produto_data(produtos)
        except Exception as e:
            print(f"[ERROR] Erro ao carregar produtos: {e}")
            produtos = []
            
        # Merge com validação
        if pedidos_filtrados and produtos:
            df_pedidos = pd.DataFrame(pedidos_filtrados)
            df_produtos = pd.DataFrame(produtos)
            if 'id_Prod' in df_pedidos.columns and 'id_Prod' in df_produtos.columns:
                df_merged = pd.merge(
                    df_pedidos,
                    df_produtos[['id_Prod', 'nome_Prod', 'Valor_Prod']],
                    left_on='id_Prod', right_on='id_Prod', how='left', suffixes=('', '_Prod')
                )
            else:
                df_merged = df_pedidos
        else:
            df_merged = pd.DataFrame(pedidos_filtrados)
            
        colunas = ['id', 'idOrderPedido', 'qtd', 'nome_Prod', 'Valor_Prod', 'sub_total', 'pago']
        for c in colunas:
            if c not in df_merged.columns:
                df_merged[c] = ''
                
        # Calcula sub_total com validação
        if 'qtd' in df_merged.columns and 'Valor_Prod' in df_merged.columns:
            df_merged['sub_total'] = df_merged.apply(
                lambda row: safe_float_convert(row['qtd']) * safe_float_convert(row['Valor_Prod']), 
                axis=1
            )
        else:
            df_merged['sub_total'] = 0.0
            
        df_final = df_merged[colunas]
        
        # Preenche valores vazios
        if 'nome_Prod' in df_final.columns:
            df_final.loc[:, 'nome_Prod'] = df_final['nome_Prod'].fillna('')
        if 'Valor_Prod' in df_final.columns:
            df_final.loc[:, 'Valor_Prod'] = df_final['Valor_Prod'].fillna('')
            
        # Calcula totais com validação
        try:
            total_nao_pagos = df_final.loc[df_final['pago']==0, 'sub_total'].sum() if not df_final.empty else 0.0
            total_pagos = df_final.loc[df_final['pago']==1, 'sub_total'].sum() if not df_final.empty else 0.0
            saldo = total_nao_pagos
        except Exception as e:
            print(f"[WARN] Erro no cálculo de totais: {e}")
            total_nao_pagos = total_pagos = saldo = 0.0
            
        totais_nao_pagos.value = f"{total_nao_pagos:.2f}"
        totais_pagos.value = f"{total_pagos:.2f}"
        saldo_devedor.value = f"{saldo:.2f}"
        
        columns = [ft.DataColumn(ft.Text(str(key))) for key in colunas]
        rows = []
        
        for _, row in df_final.iterrows():
            row_id = row.get("id")
            row_cells = [ft.DataCell(ft.Text(str(row.get(key, "")))) for key in ['id', 'idOrderPedido', 'qtd', 'nome_Prod', 'Valor_Prod', 'sub_total']]
            
            # Cria uma função de callback para capturar corretamente o row_id
            def create_checkbox_handler(current_row_id):
                def handler(e):
                    atualizar_status(current_row_id, "pago", 1 if e.control.value else 0)
                return handler
            
            row_cells += [
                ft.DataCell(ft.Checkbox(
                    value=bool(row.get("pago", 0)), 
                    on_change=create_checkbox_handler(row_id)
                ))
            ]
            rows.append(ft.DataRow(row_cells))
            
        if not rows:
            rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
            
        tabela.current.columns = columns
        tabela.current.rows = rows
        page.update()

    dropdown_numpedidos = ft.Dropdown(
        ref=selected_num_pedido,
        options=opcoes_numpedidos,
        label="Número do Pedido",
        width=250,
        on_change=filtrar_pedidos
    )
    columns = [ft.DataColumn(ft.Text("id"))] + [ft.DataColumn(ft.Text(col)) for col in ['idOrderPedido', 'qtd', 'nome_Prod', 'Valor_Prod', 'sub_total', 'pago']]
    rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
    tabela_inicial = ft.DataTable(ref=tabela, columns=columns, rows=rows, expand=True)
    botao_pdf = ft.ElevatedButton("Gerar PDF (local)", on_click=lambda e: gerar_pdf_pedido())
    botao_exportar = ft.ElevatedButton("Exportar PDF Servidor", on_click=exportar_pdf_servidor)
    # Callback de teste rápido para verificar clique (não interfere na lógica principal)
    def clique_enviar(e):
        print('[DEBUG] Botão Enviar clicado (função dedicada)')
        enviar_pdf_cliente(e)
    botao_enviar = ft.ElevatedButton("Enviar ao Cliente", on_click=clique_enviar, disabled=False, tooltip="Enviar PDF via WhatsApp")
    
    # Botão para marcar todos os itens do pedido como pagos
    botao_marcar_pagos = ft.ElevatedButton(
        "Marcar Todos Pagos", 
        on_click=marcar_todos_pagos, 
        tooltip="Marca todos os itens do pedido selecionado como pagos",
        color="green"
    )
    # Usa ResponsiveRow para distribuir controles e permitir quebra
    controles_topo = ft.ResponsiveRow([
        ft.Container(dropdown_numpedidos, col={'xs':12,'sm':6,'md':3}),
        ft.Container(totais_nao_pagos, col={'xs':6,'sm':4,'md':2}),
        ft.Container(totais_pagos, col={'xs':6,'sm':4,'md':2}),
        ft.Container(saldo_devedor, col={'xs':6,'sm':4,'md':2}),
        ft.Container(botao_pdf, col={'xs':6,'sm':4,'md':2}),
        ft.Container(botao_exportar, col={'xs':6,'sm':4,'md':2}),
        ft.Container(botao_enviar, col={'xs':6,'sm':4,'md':2}),
        ft.Container(botao_marcar_pagos, col={'xs':6,'sm':4,'md':2}),
    ], spacing=10, run_spacing=10)
    return ft.Column([
        texto_titulo("Lista de Pedidos Temporários"),
        texto_padrao("Selecione um número de pedido para visualizar os detalhes."),
        controles_topo,
        tabela_inicial,
        msg_pdf
    ], scroll=ft.ScrollMode.AUTO, width=1100, height=500)
