import flet as ft

def main(page: ft.Page):
    page.title = "Teste FilePicker"
    
    # Variável para armazenar o arquivo selecionado
    arquivo_selecionado = ft.Text("Nenhum arquivo selecionado", color="grey")
    
    def on_file_result(e):
        print(f"Resultado do FilePicker: {e.files}")
        if e.files:
            arquivo = e.files[0]
            arquivo_selecionado.value = f"Arquivo selecionado: {arquivo.name}"
            arquivo_selecionado.color = "green"
            print(f"Caminho do arquivo: {arquivo.path}")
        else:
            arquivo_selecionado.value = "Nenhum arquivo selecionado"
            arquivo_selecionado.color = "grey"
        page.update()
    
    # Criar FilePicker
    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)
    
    def abrir_file_picker(e):
        print("Botão clicado - abrindo FilePicker...")
        try:
            file_picker.pick_files(
                dialog_title="Selecionar arquivo PDF",
                allowed_extensions=["pdf"],
                allow_multiple=False
            )
            print("FilePicker chamado com sucesso!")
        except Exception as ex:
            print(f"Erro: {ex}")
    
    # Criar botão
    botao = ft.ElevatedButton(
        "📁 Selecionar PDF",
        on_click=abrir_file_picker
    )
    
    # Adicionar componentes à página
    page.add(
        ft.Column([
            ft.Text("Teste do FilePicker", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            botao,
            arquivo_selecionado
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)
