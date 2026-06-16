# core/month_operations.py
from nicegui import ui
import core.state as state
from storage import save_data, load_data, delete_month
from core.tree_builder import refresh_ui
from logger import log_call, log
from datetime import datetime
from models import CategoryNode

def update_month_selector():
    if state.month_select:
        state.month_select.options = state.available_months
        if state.current_month in state.available_months:
            state.month_select.value = state.current_month
        else:
            state.month_select.value = None

@log_call()
def change_month(month):
    if not month or month == state.current_month:
        return
    save_data(state.incomes, state.root_expenses, state.root_investments, state.current_month)
    incomes, root_expenses, root_investments, current_month, _ = load_data(month)
    state.incomes, state.root_expenses, state.root_investments, state.current_month = incomes, root_expenses, root_investments, current_month
    refresh_ui()
    manual_save()
    ui.notify(f"Загружен месяц {month}", type="info")

@log_call()
def create_new_month():
    with ui.dialog() as dialog, ui.card():
        ui.label("Новый месяц")
        new_month_input = ui.input("Месяц (YYYY-MM)", placeholder="2025-02", value=datetime.now().strftime("%Y-%m"))
        copy_checkbox = ui.checkbox("Скопировать данные из текущего месяца")
        def confirm():
            new_month = new_month_input.value
            if not new_month or len(new_month) != 7 or new_month[4] != '-':
                ui.notify("Неверный формат. Используйте ГГГГ-ММ", type="warning")
                return
            if new_month in state.available_months:
                ui.notify("Месяц уже существует", type="warning")
                return
            # Сохраняем текущий месяц перед созданием нового
            save_data(state.incomes, state.root_expenses, state.root_investments, state.current_month)
            if copy_checkbox.value:
                # Копируем детей корня расходов
                new_expenses_dict = {}
                for child in state.root_expenses.children:
                    new_expenses_dict[child.name] = child.to_dict(for_expense=True)
                new_investments_dict = {}
                for child in state.root_investments.children:
                    new_investments_dict[child.name] = child.to_dict(for_expense=False)
                new_root_exp = CategoryNode("__ROOT_EXPENSES__")
                new_root_inv = CategoryNode("__ROOT_INVESTMENTS__")
                for name, data in new_expenses_dict.items():
                    child_node = CategoryNode.from_dict(name, data, for_expense=True, parent=new_root_exp)
                    new_root_exp.add_child(child_node)
                for name, data in new_investments_dict.items():
                    child_node = CategoryNode.from_dict(name, data, for_expense=False, parent=new_root_inv)
                    new_root_inv.add_child(child_node)
                save_data(state.incomes, new_root_exp, new_root_inv, new_month)
            else:
                # Пустой месяц
                new_root_exp = CategoryNode("__ROOT_EXPENSES__")
                new_root_inv = CategoryNode("__ROOT_INVESTMENTS__")
                save_data({}, new_root_exp, new_root_inv, new_month)
            # Обновляем списки и текущий месяц
            state.available_months = sorted(state.available_months + [new_month])
            state.current_month = new_month
            incomes, root_expenses, root_investments, _, _ = load_data(new_month)
            state.incomes, state.root_expenses, state.root_investments = incomes, root_expenses, root_investments
            update_month_selector()
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"Создан месяц {new_month}", type="positive")
        ui.button("Создать", on_click=confirm)
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()
    
@log_call()
def delete_current_month():
    if not state.current_month:
        ui.notify("Нет текущего месяца для удаления", type="warning")
        return
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Удалить месяц {state.current_month}?")
        ui.label("Все данные за этот месяц будут удалены.").classes("text-caption")
        with ui.row():
            def confirm(month=state.current_month):
                log(f"delete_current_month: вызываем delete_month({month})", level="INFO")
                success = delete_month(month)
                log(f"delete_current_month: результат delete_month = {success}", level="INFO")
                if success:
                    incomes, root_expenses, root_investments, current_month, available_months = load_data()
                    state.incomes, state.root_expenses, state.root_investments, state.current_month, state.available_months = incomes, root_expenses, root_investments, current_month, available_months
                    update_month_selector()
                    refresh_ui()
                    ui.notify(f"Месяц {month} удалён", type="positive")
                else:
                    ui.notify("Не удалось удалить месяц", type="negative")
                dialog.close()
            ui.button("Удалить", on_click=confirm).props("color=negative")
            ui.button("Отмена", on_click=dialog.close)
    dialog.open()

@log_call()
def manual_save():
    total_incomes = sum(state.incomes.values())
    log(f"manual_save: month={state.current_month}, total_incomes={total_incomes}, forecast={state.root_expenses.total_forecast()}, actual={state.root_expenses.total_actual()}", level="INFO")
    save_data(state.incomes, state.root_expenses, state.root_investments, state.current_month)
    try:
        ui.notify("Данные сохранены", type="positive")
    except RuntimeError:
        pass  # Игнорируем ошибку, если контекст уже удалён