import flet as ft
from models.chat_history_api import ChatHistoryAPI
from models.human_response_whats import HumanResponseWhatsSender
from models.session_agent_api import SessionAgentAPI
import requests

API_URL = "https://www.lepapon.com.br/api"
chat_api = ChatHistoryAPI(API_URL)
human_sender = HumanResponseWhatsSender(API_URL)
session_agent_api = SessionAgentAPI(API_URL)

def chat_history_view(page: ft.Page):
    page.title = "Histórico de Conversa (Gemini & Usuário)"
    messages_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=False, height=500)
    sessions_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=False, height=500)

    # Função para abrir áudio em janela modal
    def open_audio_dialog(audio_url):
        audio_player = ft.Audio(
            src=audio_url,
            autoplay=False,
            volume=1,
            balance=0,
            playback_rate=1,
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Player de Áudio"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Reproduzir áudio:", size=14),
                    audio_player,
                    ft.Row([
                        ft.ElevatedButton(
                            "▶️ Play", 
                            on_click=lambda e: audio_player.play()
                        ),
                        ft.ElevatedButton(
                            "⏸️ Pause", 
                            on_click=lambda e: audio_player.pause()
                        ),
                        ft.ElevatedButton(
                            "⏹️ Parar", 
                            on_click=lambda e: audio_player.pause()
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=10),
                width=300,
                height=150,
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: close_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        def close_dialog():
            audio_player.pause()
            page.close(dialog)
            page.update()
        
        page.open(dialog)
        page.update()

    def on_sender_change(e):
        session_id = selected_session_id.get('value')
        if not session_id:
            msg_form.value = "Nenhuma sessão selecionada para alterar o controle."
            msg_form.color = ft.Colors.ORANGE
            msg_form.visible = True
            page.update()
            return

        try:
            if e.control.value == "atendente":
                print(f"Assumindo controle da sessão: {session_id}")  # Debug: verificar o session_id
                response = session_agent_api.takeOver({'session_id': session_id})
                print(response)  # Debug: verificar a resposta da API
                msg_form.value = f"Controle da sessão assumido pelo atendente."
                msg_form.color = "green"
            elif e.control.value == "gemini":
                print(f"Liberando controle da sessão: {session_id}")
                response = session_agent_api.release({'session_id': session_id})
                print(response)  # Debug: verificar a resposta da API
                msg_form.value = f"Controle da sessão liberado para o Gemini."
                msg_form.color = "green"
            
            msg_form.visible = True
        except Exception as ex:
            msg_form.value = f"Erro ao alterar controle: {ex}"
            msg_form.color = "red"
            msg_form.visible = True
        
        page.update()

    sender_dd = ft.Dropdown(
        options=[ft.dropdown.Option("atendente", "Atendente"), ft.dropdown.Option("gemini", "Gemini")],
        value="gemini",
        color=ft.Colors.BLACK,
        on_change=on_sender_change,
    )
    text_input = ft.TextField(label="Digite a mensagem", expand=True, color=ft.Colors.BLACK, on_change=lambda e: on_text_change(e))
    send_btn = ft.ElevatedButton("Enviar", disabled=True, color=ft.Colors.PRIMARY)
    msg_form = ft.Text(visible=False)
    selected_session_id = {'value': None}
    all_sessions = {'list': []}

    def show_session_messages(session_id):
        messages_column.controls.clear()
        #print(all_sessions['list'])  # Debug: verificar as sessões carregadas
        # Agrupa todas as mensagens de sessões com o mesmo session_id (que é o phone)
        sessions = [s for s in all_sessions['list'] if s.get('session_id') == session_id]
        
        #print(sessions)  # Debug: verificar as sessões filtradas
        
        if not sessions:
            messages_column.controls.append(ft.Text("Nenhuma mensagem nesta sessão."))
        else:
            for msg in sessions:
                controls = []
                #print(f"Mensagem: {msg}")  # Debug: verificar cada mensagem
                if not msg.get("text") == 'None':
                    # Adiciona o texto da mensagem
                    controls.append(
                        ft.Text(f"{'Usuário' if msg['sender']=='user' else 'Gemini'}: {msg.get('text','')}")
                    )
                if msg.get("media_type") == "image" and msg.get("media_url"):
                    controls.append(
                        ft.Image(src=f"{API_URL}/media/{msg['media_url']}", width=200)
                    )
                if msg.get("media_type") == "audio" and msg.get("media_url"):
                    # Botão para abrir áudio em janela modal
                    audio_url = f"{API_URL}/media/{msg['media_url']}"
                    controls.append(
                        ft.Row([
                            ft.Icon(ft.Icons.AUDIOTRACK, color=ft.Colors.BLUE),
                            ft.ElevatedButton(
                                "🔊 Reproduzir Áudio",
                                on_click=lambda e, url=audio_url: open_audio_dialog(url),
                                icon=ft.Icons.PLAY_ARROW
                            )
                        ])
                    )
                controls.append(
                    ft.Text(msg.get("created_at", ""), size=10, color=ft.Colors.GREY)
                )
                messages_column.controls.append(ft.Column(controls, spacing=5))
        page.update()

    def on_session_click(e):
        selected_session_id['value'] = e.control.data
        show_session_messages(e.control.data)
        msg_form.visible = False
        page.update()

    def fetch_sessions():
        sessions_column.controls.clear()
        try:
            sessions = chat_api.get_history_by_session()
            all_sessions['list'] = sessions
            # Agrupa por session_id único (que é o phone)
            seen = set()
            for session in sessions:
                session_id = session.get('session_id', 'Sessão desconhecida')
                if session_id in seen:
                    continue
                seen.add(session_id)
                btn = ft.TextButton(f"WhatsApp: {session_id}", data=session_id, on_click=on_session_click)
                sessions_column.controls.append(btn)
            if sessions:
                # Mostra a primeira sessão por padrão
                unique_sessions = [s.get('session_id', 'Sessão desconhecida') for s in sessions if s.get('session_id', 'Sessão desconhecida') in seen]
                selected_session_id['value'] = unique_sessions[0] if unique_sessions else None
                show_session_messages(selected_session_id['value'])
            else:
                messages_column.controls.clear()
                messages_column.controls.append(ft.Text("Nenhuma sessão encontrada."))
            page.update()
        except Exception as e:
            msg_form.value = f"Erro ao buscar sessões: {e}"
            msg_form.color = "red"
            msg_form.visible = True
            page.update()

    def on_text_change(e):
        send_btn.disabled = not (text_input.value or "").strip()
        page.update()

    def send_message(e):
        send_btn.disabled = True
        page.update()
        try:
            # Envia mensagem para o chat
            chat_api.send_message(sender_dd.value, text_input.value, session_id=selected_session_id['value'])
            # O session_id é o phone
            phone = selected_session_id['value']
            if phone:
                # Envia mensagem para o WhatsApp Business API via backend usando HumanResponseWhatsSender
                try:
                    data = {"to": phone, "text": text_input.value}
                    send_human = human_sender.send_response(data)
                    print(f"Mensagem enviada para WhatsApp: {send_human}")  # Debug
                except Exception as wex:
                    msg_form.value = f"Mensagem salva, mas erro ao enviar WhatsApp: {wex}"
                    msg_form.color = "orange"
                    msg_form.visible = True
            else:
                msg_form.value = "Mensagem salva, mas sessão não possui número de telefone para WhatsApp."
                msg_form.color = "orange"
                msg_form.visible = True
            text_input.value = ""
            fetch_sessions()
            msg_form.value = msg_form.value or "Mensagem enviada com sucesso!"
            msg_form.color = msg_form.color or "green"
            msg_form.visible = True
        except Exception as ex:
            msg_form.value = f"Erro ao enviar: {ex}"
            msg_form.color = "red"
            msg_form.visible = True
        page.update()

    def delete_all_history(e):
        try:
            chat_api.delete_history()
            msg_form.value = "Todo o histórico de conversas foi deletado."
            msg_form.color = "green"
            msg_form.visible = True
            fetch_sessions()  # Atualiza a lista de sessões, que agora deve estar vazia
        except Exception as ex:
            msg_form.value = f"Erro ao deletar o histórico: {ex}"
            msg_form.color = "red"
            msg_form.visible = True
        page.update()

    text_input.on_change = on_text_change
    send_btn.on_click = send_message

    fetch_sessions()

    # Botão para atualização manual
    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Atualizar conversas",
        on_click=lambda e: fetch_sessions()
    )

    delete_button = ft.IconButton(
        icon=ft.Icons.DELETE_FOREVER,
        tooltip="Deletar todo o histórico",
        on_click=delete_all_history,
        icon_color="red"
    )

    return ft.Row([
        ft.Column([
            ft.Row([
                ft.Text("Sessões", style=ft.TextThemeStyle.HEADLINE_SMALL),
                refresh_button,
                delete_button
            ]),
            ft.Divider(),
            sessions_column
        ], expand=1),
        ft.VerticalDivider(width=2),
        ft.Column([
            ft.Text("Chat da Sessão", style=ft.TextThemeStyle.HEADLINE_SMALL),
            ft.Container(
                content=ft.Row([
                    sender_dd,
                    text_input,
                    send_btn
                ]),
                bgcolor="#f5f5f5",
                padding=10,
                border_radius=8,
            ),
            msg_form,
            ft.Divider(),
            messages_column
        ], expand=2)
    ])