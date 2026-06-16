# core/tree_builder.py
from nicegui import ui
import core.state as state
from core.report import update_report

def build_expenses_tree(container, node, level=0):
    from core.dialogs import (
        edit_forecast_dialog,
        edit_actual_dialog,
        confirm_delete_category,
        show_quick_edit_dialog
    )
    for child in node.children:
        indent = " " * level
        forecast_val = child.total_forecast()
        actual_val = child.total_actual()
        diff = forecast_val - actual_val
        text = f"{indent}📂 {child.name}: {forecast_val:.2f} / {actual_val:.2f} ({diff:+.2f})"
        with container:
            label = ui.label(text).classes("cursor-pointer").style("padding: 2px;")
            with ui.context_menu() as menu:
                ui.menu_item("✏️ Редактировать прогноз", lambda n=child: edit_forecast_dialog(n))
                ui.menu_item("📝 Редактировать факт", lambda n=child: edit_actual_dialog(n))
                ui.menu_item("🗑️ Удалить категорию", lambda n=child: confirm_delete_category(n, is_expense=True))
            label.on('contextmenu', menu.open)
            label.on('click', lambda e, n=child: show_quick_edit_dialog(n, is_expense=True))
        build_expenses_tree(container, child, level+1)

def build_investments_tree(container, node, level=0):
    from core.dialogs import (
        edit_investment_amount_dialog,
        edit_investment_category_dialog,   # <--- добавили
        confirm_delete_category,
        show_quick_edit_dialog
    )
    for child in node.children:
        indent = " " * level
        total = child.total_amount()
        text = f"{indent}💰 {child.name}: {total:.2f}"
        with container:
            label = ui.label(text).classes("cursor-pointer").style("padding: 2px;")
            with ui.context_menu() as menu:
                ui.menu_item("✏️ Редактировать сумму", lambda n=child: edit_investment_amount_dialog(n))
                ui.menu_item("✏️ Переименовать", lambda n=child: edit_investment_category_dialog(n))
                ui.menu_item("🗑️ Удалить", lambda n=child: confirm_delete_category(n, is_expense=False))
            label.on('contextmenu', menu.open)
            label.on('click', lambda e, n=child: show_quick_edit_dialog(n, is_expense=False))
        build_investments_tree(container, child, level+1)

def refresh_ui():
    if state.expenses_container is not None:
        state.expenses_container.clear()
        build_expenses_tree(state.expenses_container, state.root_expenses)
    if state.investments_container is not None:
        state.investments_container.clear()
        build_investments_tree(state.investments_container, state.root_investments)
    update_report()