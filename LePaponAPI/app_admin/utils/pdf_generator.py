"""
Gerador de PDFs com cabeçalho padrão para o sistema LePapon
"""
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class PDFGenerator:
    """Classe para gerar PDFs com cabeçalho padrão"""
    
    def __init__(self):
        self.empresa_nome = "LePapon Lanches - Claudemir"
        self.empresa_endereco = "Endereço: João Venâncio Girarde, nº 260"
        self.empresa_cnpj = "CNPJ: 33.794.253/0001-33   Fone: (55) 5499-2635135"
        
    def criar_cabecalho(self, canvas_obj, titulo, logo_path=None):
        """
        Cria o cabeçalho padrão no PDF
        """
        width, height = A4
        
        # Logo
        if not logo_path:
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../acents/L.png'))
        
        try:
            canvas_obj.drawImage(logo_path, 40, height-100, width=60, height=60, preserveAspectRatio=True, mask='auto')
        except Exception:
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.drawString(40, height-100, f"[Logo não encontrado: {logo_path}]")
        
        # Dados da empresa
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(110, height-60, self.empresa_nome)
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(110, height-80, self.empresa_endereco)
        canvas_obj.drawString(110, height-95, self.empresa_cnpj)
        
        # Data do relatório
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(400, height-60, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}")
        
        # Título do relatório
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(40, height-120, titulo)
        
        return height-150  # Retorna a posição Y após o cabeçalho
    
    def criar_tabela(self, canvas_obj, y_inicial, colunas_legenda, larguras_colunas, dados):
        """
        Cria uma tabela no PDF
        """
        canvas_obj.setFont("Helvetica", 10)
        y = y_inicial
        
        # Calcula posições X das colunas
        x_positions = [40]
        for w in larguras_colunas[:-1]:
            x_positions.append(x_positions[-1] + w)
        
        # Cabeçalho da tabela
        for i, (campo, legenda) in enumerate(colunas_legenda.items()):
            canvas_obj.drawString(x_positions[i], y, legenda)
        y -= 20
        
        # Dados da tabela
        total = 0.0
        for _, row in dados.iterrows():
            for i, campo in enumerate(colunas_legenda.keys()):
                valor = str(row.get(campo, ""))
                canvas_obj.drawString(x_positions[i], y, valor)
                
                # Soma valores se for campo de valor
                if 'valor' in campo.lower() or 'total' in campo.lower():
                    try:
                        total += float(str(row.get(campo, 0)).replace(",", "."))
                    except:
                        pass
            
            y -= 18
            if y < 60:
                canvas_obj.showPage()
                y = A4[1] - 40
        
        return y, total
    
    def finalizar_pdf(self, canvas_obj, y_atual, total, moeda="R$"):
        """
        Finaliza o PDF com o total
        """
        # Total
        if y_atual < 80:
            canvas_obj.showPage()
            y_atual = A4[1] - 40
        
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawString(40, y_atual-10, f"Total do período: {moeda} {total:.2f}")
        canvas_obj.save()
    
    def gerar_pdf_completo(self, dados, titulo, nome_arquivo, colunas_legenda, larguras_colunas):
        """
        Gera um PDF completo com dados
        """
        # Cria o canvas
        c = canvas.Canvas(nome_arquivo, pagesize=A4)
        
        # Cria cabeçalho
        y_atual = self.criar_cabecalho(c, titulo)
        
        # Cria tabela
        y_atual, total = self.criar_tabela(c, y_atual, colunas_legenda, larguras_colunas, dados)
        
        # Finaliza PDF
        self.finalizar_pdf(c, y_atual, total)
        
        return nome_arquivo
