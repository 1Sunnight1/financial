# core/dialogs.py
from nicegui import ui
from datetime import datetime
import core.state as state
from core.tree_builder import refresh_ui
from core.month_operations import manual_save
from operations import add_expense_category, add_investment_category, add_daily_expense, set_actual_expense
from logger import log_call, log
from core.utils import get_all_expense_paths, get_all_investment_paths

# ----------------------------------------------------------------------
# Диалоги редактирования и удаления
# ----------------------------------------------------------------------

@log_call()
def edit_forecast_dialog(category):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Редактировать прогноз: {category.name}")
        forecast_input = ui.number("Прогноз", value=category.forecast if category.forecast is not None else 0.0, step=100)
        def save():
            category.forecast = forecast_input.value
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"Прогноз для {category.name} обновлён", type="positive")
        ui.button("Сохранить", on_click=save)
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()

@log_call()
def edit_actual_dialog(category):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Редактировать факт: {category.name}")
        actual_input = ui.number("Факт", value=category.actual if category.actual is not None else 0.0, step=100)
        def save():
            category.actual = actual_input.value
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"Факт для {category.name} обновлён", type="positive")
        ui.button("Сохранить", on_click=save)
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()

@log_call()
def edit_investment_amount_dialog(category):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Редактировать инвестицию: {category.name}")
        amount_input = ui.number("Сумма", value=category.amount, step=1000)
        def save():
            category.amount = amount_input.value
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"Сумма для {category.name} обновлена", type="positive")
        ui.button("Сохранить", on_click=save)
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()

@log_call()
def edit_investment_category_dialog(category):
    """Диалог переименования категории инвестиций"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Переименовать инвестиционную категорию: {category.name}")
        new_name_input = ui.input("Новое название", value=category.name)
        def save():
            new_name = new_name_input.value.strip()
            if not new_name:
                ui.notify("Название не может быть пустым", type="warning")
                return
            parent = category.parent
            if parent:
                for child in parent.children:
                    if child.name == new_name and child is not category:
                        ui.notify(f"Категория с именем '{new_name}' уже существует", type="warning")
                        return
                category.name = new_name
                from core.tree_builder import refresh_ui
                from core.month_operations import manual_save
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify(f"Категория переименована в '{new_name}'", type="positive")
            else:
                ui.notify("Ошибка: у категории нет родителя", type="negative")
        ui.button("Сохранить", on_click=save)
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()
    
@log_call()
def confirm_delete_category(category, is_expense=True):
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Удалить категорию '{category.name}'?")
        ui.label("Все подкатегории также будут удалены.").classes("text-caption")
        def delete():
            parent = category.parent
            if parent:
                parent.children.remove(category)
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"Категория '{category.name}' удалена", type="warning")
        ui.button("Удалить", on_click=delete).props("color=negative")
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()

def show_quick_edit_dialog(category, is_expense=True):
    with ui.dialog() as dialog, ui.card().style("width: 500px"):
        ui.label(f"Редактирование: {category.name}").classes("text-h6")
        if is_expense:
            forecast_val = category.forecast if category.forecast is not None else 0.0
            actual_val = category.total_actual()
            forecast_input = ui.number("Прогноз", value=forecast_val, step=100)
            if category.daily:
                ui.label("Ежедневные записи:").classes("text-subtitle1")
                daily_list = ui.column()
                for date_str, amt in sorted(category.daily.items()):
                    with daily_list:
                        ui.label(f"{date_str}: {amt:.2f}").classes("text-caption")
            else:
                ui.label("Нет дневных записей").classes("text-caption")
            def save():
                category.forecast = forecast_input.value
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify("Прогноз обновлён", type="positive")
            ui.button("Сохранить прогноз", on_click=save)
        else:
            amount_input = ui.number("Сумма", value=category.amount, step=1000)
            def save():
                category.amount = amount_input.value
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify("Сумма обновлена", type="positive")
            ui.button("Сохранить", on_click=save)
        ui.button("Закрыть", on_click=dialog.close)
    dialog.open()

# ----------------------------------------------------------------------
# Диалоги добавления
# ----------------------------------------------------------------------

@log_call()
def show_add_expense_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("➕ Добавить категорию расходов")
        path_input = ui.input("Путь (через слэш)", placeholder="Еда/Рестораны/Обеды", autocomplete=get_all_expense_paths())
        forecast_input = ui.number("Прогноз", value=0.0, step=100)
        with ui.row():
            def add():
                path_str = path_input.value.strip()
                if not path_str:
                    ui.notify("Введите путь", type="warning")
                    return
                path = [p.strip() for p in path_str.split('/') if p.strip()]
                forecast = forecast_input.value
                add_expense_category(path, forecast, state.root_expenses)
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify(f"✅ Категория '{path_str}' добавлена", type="positive")
            ui.button("Добавить", on_click=add, icon="add")
            ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

@log_call()
def show_add_investment_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("➕ Добавить инвестицию")
        path_input = ui.input("Путь (через слэш)", placeholder="Акции/Российские", autocomplete=get_all_investment_paths())
        amount_input = ui.number("Сумма", value=0.0, step=1000)
        def add():
            path_str = path_input.value.strip()
            if not path_str:
                ui.notify("Введите путь", type="warning")
                return
            path = [p.strip() for p in path_str.split('/') if p.strip()]
            amount = amount_input.value
            add_investment_category(path, amount, state.root_investments)
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"✅ Инвестиция '{path_str}' добавлена", type="positive")
        ui.button("Добавить", on_click=add, icon="add")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

@log_call()
def show_set_actual_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("📝 Записать фактический расход")
        path_input = ui.input("Путь к категории", placeholder="Еда/Рестораны", autocomplete=get_all_expense_paths())
        ui.label("Дата")
        date_input = ui.date(value=datetime.now().strftime("%Y-%m-%d"))
        actual_input = ui.number("Сумма", value=0.0, step=100)
        def set_act():
            path_str = path_input.value.strip()
            if not path_str:
                ui.notify("Введите путь", type="warning")
                return
            path = [p.strip() for p in path_str.split('/') if p.strip()]
            amount = actual_input.value
            date_str = date_input.value
            try:
                add_daily_expense(path, date_str, amount, state.root_expenses)
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify(f"✅ Запись {amount} за {date_str} добавлена", type="positive")
            except ValueError as e:
                ui.notify(str(e), type="negative")
        ui.button("Записать", on_click=set_act, icon="edit")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

# ----------------------------------------------------------------------
# Диалоги для доходов
# ----------------------------------------------------------------------

@log_call()
def show_add_incomes_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("💰 Добавить доход")
        ui.label("Дата")
        date_input = ui.date(value=datetime.now().strftime("%Y-%m-%d"))
        amount_input = ui.number("Сумма", value=0.0, step=100)
        def add():
            date_str = date_input.value
            amount = amount_input.value
            if amount <= 0:
                ui.notify("Сумма должна быть больше 0", type="warning")
                return
            if date_str in state.incomes:
                state.incomes[date_str] += amount
            else:
                state.incomes[date_str] = amount
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"✅ Доход {amount} за {date_str} добавлен", type="positive")
        ui.button("Добавить", on_click=add, icon="add")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

def show_incomes_dialog():
    if not state.incomes:
        ui.notify("Нет записей о доходах", type="warning")
        return
    with ui.dialog() as dialog, ui.card().style("width: 500px"):
        ui.label("📋 Доходы за месяц").classes("text-h6")
        for date_str, amt in sorted(state.incomes.items()):
            with ui.row().classes("w-full items-center"):
                ui.label(f"{date_str}: {amt:.2f}").classes("grow")
                ui.button(icon="delete", on_click=lambda d=date_str: delete_incomes_transaction(d, dialog)).props("flat").props("color=negative")
        ui.button("Закрыть", on_click=dialog.close)
    dialog.open()

@log_call()
def delete_incomes_transaction(date_str, dialog):
    if date_str in state.incomes:
        del state.incomes[date_str]
        refresh_ui()
        manual_save()
        dialog.close()
        ui.notify(f"Доход за {date_str} удалён", type="positive")