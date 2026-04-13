from pathlib import Path
from nicegui import ui


def register_theme() -> None:
    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />')
    ui.colors(primary='#0B8A66', secondary='#6BE6A8', accent='#6D63D6', positive='#0B8A66', negative='#D84C4C')
    ui.add_css(Path('app/static/styles.css').read_text(encoding='utf-8'))
