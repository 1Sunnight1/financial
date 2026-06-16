# ui/settings_tab.py
from nicegui import ui
from logger import LOGGING_ENABLED, set_logging_enabled

def create_settings_tab(tab_panels):
    with tab_panels:
        with ui.tab_panel('Настройки'):
            ui.label("⚙️ Настройки приложения").classes("text-h6 q-pa-md")
            ui.switch('Логирование (запись в файл)', value=LOGGING_ENABLED, on_change=lambda e: set_logging_enabled(e.value))
            ui.label("Логи сохраняются в папке logs/").classes("text-caption")