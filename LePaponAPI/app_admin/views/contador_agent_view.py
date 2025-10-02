import flet as ft
from utils.agent_contador import ContadorAgent

BASE_URL = "http://lepapon.api:3000"


def contador_agent_view(page: ft.Page):
    agent = ContadorAgent(BASE_URL)

    pergunta = ft.TextField(label="Pergunte ao Agente Contábil", hint_text="Ex.: Como foi o caixa ontem?", expand=True)
    resposta = ft.Text(value="", selectable=True)

    def on_send(e=None):
        try:
            texto = pergunta.value or "hoje"
            out = agent.responder(texto)
            resposta.value = out
            resposta.color = "black"
        except Exception as ex:
            resposta.value = f"Erro: {ex}"
            resposta.color = "red"
        page.update()

    return ft.Column([
        ft.Text("Agente Contábil", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            pergunta,
            ft.ElevatedButton("Perguntar", on_click=on_send),
        ]),
        ft.Divider(),
        resposta,
    ], expand=True)
