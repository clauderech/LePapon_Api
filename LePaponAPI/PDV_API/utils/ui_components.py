import flet as ft

def create_filter_field(label: str, on_change, width: int = 250, hint: str = "Digite para filtrar") -> ft.TextField:
    return ft.TextField(
        label=label,
        width=width,
        hint_text=hint,
        on_change=on_change,
        dense=True,
        height=48
    )
