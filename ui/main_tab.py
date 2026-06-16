# ui/main_tab.py
from nicegui import ui
import core.state as state
from core.month_operations import change_month, create_new_month, delete_current_month
from core.dialogs import (
    show_add_expense_dialog,
    show_add_investment_dialog,
    show_set_actual_dialog,
    show_add_incomes_dialog,
    show_incomes_dialog,
)
from core.tree_builder import refresh_ui
from core.init import init_data
from core.month_operations import manual_save

def create_main_tab(tab_panels):
    with tab_panels:
        with ui.tab_panel('Главная'):
            # Строка выбора месяца
            with ui.row().classes("w-full items-center gap-2 p-2"):
                ui.label("Месяц:").classes("text-subtitle1")
                state.month_select = ui.select(
                    state.available_months,
                    value=state.current_month,
                    on_change=lambda e: change_month(e.value)
                )
                ui.button("➕ Новый месяц", on_click=create_new_month, icon="add").props("outline")
                ui.button("🗑️ Удалить месяц", on_click=delete_current_month, icon="delete").props("outline").props("color=negative")
            # Панель кнопок
            with ui.row().classes("w-full items-center gap-2 p-2"):
                ui.button("➕ Добавить доход", on_click=show_add_incomes_dialog, icon="add").props("outline")
                ui.button("📋 Доходы", on_click=show_incomes_dialog, icon="list").props("outline")
                ui.button("Добавить расход", on_click=show_add_expense_dialog, icon="shopping_cart").props("outline")
                ui.button("Записать факт", on_click=show_set_actual_dialog, icon="edit_note").props("outline")
                ui.button("Добавить инвестицию", on_click=show_add_investment_dialog, icon="trending_up").props("outline")
                ui.button("Обновить", on_click=refresh_ui, icon="refresh").props("flat")
                ui.button("💾 Сохранить", on_click=manual_save, icon="save").props("outline")
            # Две колонки
            with ui.row().classes("w-full"):
                with ui.column().classes("w-1/2 q-pa-md"):
                    ui.label("📋 Расходы").classes("text-h6")
                    state.expenses_container = ui.column().classes("q-ml-md")
                with ui.column().classes("w-1/2 q-pa-md"):
                    ui.label("📈 Инвестиции").classes("text-h6")
                    state.investments_container = ui.column().classes("q-ml-md")
            # Отчёт
            state.report_label = ui.label().classes("text-subtitle1 q-pa-md")
            # Инициализация
            init_data()