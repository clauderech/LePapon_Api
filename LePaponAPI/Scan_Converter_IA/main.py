import flet as ft
import subprocess

def main(page: ft.Page):
    page.title = "Scan Converter IA"
    
    def run_script(script_name):
        try:
            result = subprocess.run(
                ["python3", f"Scan_Converter_IA/{script_name}"],
                capture_output=True,
                text=True
            )
            output.value = result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            output.value = f"Erro ao executar {script_name}: {e}"
        page.update()

    # Botões para cada funcionalidade
    convert_dates_button = ft.ElevatedButton(
        "Converter Datas (JSONs)",
        on_click=lambda _: run_script("convert_dates_jsons.py")
    )
    convert_pdf_button = ft.ElevatedButton(
        "Converter PDF para Texto",
        on_click=lambda _: run_script("convert_pdf_to_text_gemini.py")
    )
    send_response_button = ft.ElevatedButton(
        "Enviar Resposta para API",
        on_click=lambda _: run_script("send_response_to_api.py")
    )

    # Área de saída para logs
    output = ft.Text(value="", expand=True)

    # Layout da página
    page.add(
        ft.Column(
            [
                ft.Text("Scan Converter IA", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                convert_dates_button,
                convert_pdf_button,
                send_response_button,
                ft.Divider(),
                ft.Text("Saída:", style=ft.TextThemeStyle.HEADLINE_SMALL),
                output,
            ],
            expand=True,
        )
    )

ft.app(target=main)