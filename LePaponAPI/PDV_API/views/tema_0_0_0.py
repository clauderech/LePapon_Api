import flet as ft

# Paleta de cores do tema lanchonete
COR_PRIMARIA = "#FFB300"      # Amarelo vibrante
COR_SECUNDARIA = "#D84315"    # Vermelho apetitoso
COR_FUNDO = "#FFF8E1"         # Bege claro
COR_TEXTO = "#4E342E"         # Marrom escuro

# Caminho do logo (coloque sua imagem em assets/logo_lanchonete.png)
LOGO_PATH = "assets/L.png"

def barra_superior(titulo: str):
    return ft.AppBar(
        title=ft.Text(titulo, size=28, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        bgcolor=COR_PRIMARIA,
        center_title=True,
        leading=ft.Image(src=LOGO_PATH, width=40, height=40),
    )

def botao_acao(texto: str, on_click, icone: str = ""):
    kwargs = {
        "bgcolor": COR_PRIMARIA,
        "color": COR_SECUNDARIA,
        "style": ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=18,
        ),
        "on_click": on_click,
    }
    if icone is not None:
        kwargs["icon"] = icone
    return ft.ElevatedButton(
        texto,
        **kwargs
    )

def card_lanche(titulo: str, descricao: str, preco: float, imagem: str = "", on_click=None):
    return ft.Card(
        content=ft.Container(
            content=ft.Row([
                ft.Image(src=imagem, width=80, height=80) if imagem else ft.Icon(ft.Icons.FASTFOOD, size=60, color=COR_SECUNDARIA),
                ft.Column([
                    ft.Text(titulo, size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                    ft.Text(descricao, size=16, color=COR_TEXTO),
                    ft.Text(f"R$ {preco:.2f}", size=18, weight=ft.FontWeight.BOLD, color=COR_SECUNDARIA),
                ], spacing=4),
            ], alignment=ft.MainAxisAlignment.START),
            padding=16,
            bgcolor="#FFF3E0",
            border_radius=16,
            on_click=on_click,
        ),
        elevation=3,
    )

def texto_titulo(texto: str):
    return ft.Text(texto, size=24, weight=ft.FontWeight.BOLD, color=COR_SECUNDARIA)

def texto_padrao(texto: str):
    return ft.Text(texto, size=18, color=COR_TEXTO)

def aplicar_tema(page: ft.Page):
    page.bgcolor = COR_FUNDO
    page.fonts = {"default": "Arial"}