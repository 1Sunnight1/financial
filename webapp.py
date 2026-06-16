# webapp.py
from nicegui import ui, app
from ui.main_tab import create_main_tab
from ui.charts_tab import create_charts_tab
from ui.settings_tab import create_settings_tab

ui.page_title("Финансовый помощник")

with ui.header(elevated=True).classes("bg-primary text-white"):
    ui.label("💰 Финансовый помощник").classes("text-h4")

tabs = ui.tabs().classes('w-full')
with tabs:
    ui.tab('Главная', icon='home')
    ui.tab('Графики', icon='bar_chart')
    ui.tab('Настройки', icon='settings')

tab_panels = ui.tab_panels(tabs, value='Главная').classes('w-full')

# Контейнер для графика (создаётся здесь, чтобы был доступен)
chart_container = ui.column().classes("w-full")

create_main_tab(tab_panels)
create_charts_tab(tab_panels, chart_container)
create_settings_tab(tab_panels)

ui.run(host="127.0.0.1", port=8080, title="Финансовый помощник", reload=False)