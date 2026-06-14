# webapp.py
from nicegui import ui, app
import matplotlib.pyplot as plt
from nicegui import ui, app
from storage import load_data, save_data
from models import CategoryNode
import plotly.graph_objects as go
import copy
from datetime import datetime
from operations import add_daily_expense, add_expense_category, add_investment_category, set_actual_expense
from logger import set_logging_enabled, log
import traceback

# ---------- Глобальное состояние ----------
incomes = {}   # словарь { "YYYY-MM-DD": сумма }
root_expenses = None
root_investments = None
current_month = None
available_months = []

# Контейнеры
expenses_container = None
investments_container = None
report_label = None
month_select = None

# ---------- Вспомогательные функции ----------
def refresh_ui():
    """Полностью перестраивает деревья и отчёт"""
    expenses_container.clear()
    investments_container.clear()
    build_expenses_tree(expenses_container, root_expenses)
    build_investments_tree(investments_container, root_investments)
    update_report()

def build_expenses_tree(container, node, level=0):
    """Рекурсивно строит дерево расходов"""
    for child in node.children:
        indent = " " * level
        forecast_val = child.total_forecast()
        actual_val = child.total_actual()
        diff = forecast_val - actual_val
        text = f"{indent}📂 {child.name}: {forecast_val:.2f} / {actual_val:.2f} ({diff:+.2f})"
        with container:
            label = ui.label(text).classes("cursor-pointer").style("padding: 2px;")
            # Привязываем контекстное меню к label через on('contextmenu')
            with ui.context_menu() as menu:
                ui.menu_item("✏️ Редактировать прогноз", lambda n=child: edit_forecast_dialog(n))
                ui.menu_item("📝 Редактировать факт", lambda n=child: edit_actual_dialog(n))
                ui.menu_item("🗑️ Удалить категорию", lambda n=child: confirm_delete_category(n, is_expense=True))
            label.on('contextmenu', lambda e, m=menu: m.open(e))
            # Левый клик - быстрое редактирование
            label.on('click', lambda e, n=child: show_quick_edit_dialog(n, is_expense=True))
        # Рекурсивно обходим детей (уровень увеличиваем)
        build_expenses_tree(container, child, level+1)

def build_investments_tree(container, node, level=0):
    """Рекурсивно строит дерево инвестиций"""
    for child in node.children:
        indent = " " * level
        total = child.total_amount()
        text = f"{indent}💰 {child.name}: {total:.2f}"
        with container:
            label = ui.label(text).classes("cursor-pointer").style("padding: 2px;")
            with ui.context_menu() as menu:
                ui.menu_item("✏️ Редактировать сумму", lambda n=child: edit_investment_amount_dialog(n))
                ui.menu_item("🗑️ Удалить", lambda n=child: confirm_delete_category(n, is_expense=False))
            label.on('contextmenu', lambda e, m=menu: m.open(e))
            label.on('click', lambda e, n=child: show_quick_edit_dialog(n, is_expense=False))
        build_investments_tree(container, child, level+1)

# ---------- Диалоги редактирования ----------
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
            # Отображение дневных записей
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
    
# ---------- Диалоги добавления (улучшенные) ----------
def show_add_expense_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("➕ Добавить категорию расходов")
        path_input = ui.input("Путь (через слэш)", placeholder="Еда/Рестораны/Обеды")
        forecast_input = ui.number("Прогноз", value=0.0, step=100)
        with ui.row():
            def add():
                path_str = path_input.value.strip()
                if not path_str:
                    ui.notify("Введите путь", type="warning")
                    return
                path = [p.strip() for p in path_str.split('/') if p.strip()]
                forecast = forecast_input.value
                add_expense_category(path, forecast, root_expenses)
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify(f"✅ Категория '{path_str}' добавлена", type="positive")
            ui.button("Добавить", on_click=add, icon="add")
            ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

def show_add_investment_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("➕ Добавить инвестицию")
        path_input = ui.input("Путь (через слэш)", placeholder="Акции/Российские")
        amount_input = ui.number("Сумма", value=0.0, step=1000)
        def add():
            path_str = path_input.value.strip()
            if not path_str:
                ui.notify("Введите путь", type="warning")
                return
            path = [p.strip() for p in path_str.split('/') if p.strip()]
            amount = amount_input.value
            add_investment_category(path, amount, root_investments)
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"✅ Инвестиция '{path_str}' добавлена", type="positive")
        ui.button("Добавить", on_click=add, icon="add")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

def show_set_actual_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("📝 Записать фактический расход")
        path_input = ui.input("Путь к категории", placeholder="Еда/Рестораны")
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
                add_daily_expense(path, date_str, amount, root_expenses)
                refresh_ui()
                manual_save()
                dialog.close()
                ui.notify(f"✅ Запись {amount} за {date_str} добавлена", type="positive")
            except ValueError as e:
                ui.notify(str(e), type="negative")
        ui.button("Записать", on_click=set_act, icon="edit")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

# ---------- Диалоги для доходов ----------
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
            global incomes
            if date_str in incomes:
                incomes[date_str] += amount
            else:
                incomes[date_str] = amount
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"✅ Доход {amount} за {date_str} добавлен", type="positive")
        ui.button("Добавить", on_click=add, icon="add")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

def show_incomes_dialog():
    if not incomes:
        ui.notify("Нет записей о доходах", type="warning")
        return
    with ui.dialog() as dialog, ui.card().style("width: 500px"):
        ui.label("📋 Доходы за месяц").classes("text-h6")
        for date_str, amt in sorted(incomes.items()):
            with ui.row().classes("w-full items-center"):
                ui.label(f"{date_str}: {amt:.2f}").classes("grow")
                ui.button(icon="delete", on_click=lambda d=date_str: delete_incomes_transaction(d, dialog)).props("flat").props("color=negative")
        ui.button("Закрыть", on_click=dialog.close)
    dialog.open()

def delete_incomes_transaction(date_str, dialog):
    global incomes
    if date_str in incomes:
        del incomes[date_str]
        refresh_ui()
        manual_save()
        dialog.close()
        ui.notify(f"Доход за {date_str} удалён", type="positive")

# ---------- График ----------
def show_chart_dialog():
    """Показывает интерактивный график сравнения прогноза и факта по расходам"""
    # Собираем данные по прямым детям root_expenses
    categories = []
    forecasts = []
    actuals = []
    for child in root_expenses.children:
        categories.append(child.name)
        forecasts.append(child.total_forecast())
        actuals.append(child.total_actual())
    if not categories:
        ui.notify("Нет категорий расходов для отображения графика", type="warning")
        return

    # Создаём фигуру Plotly
    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories, y=forecasts, name='Прогноз', marker_color='skyblue'))
    fig.add_trace(go.Bar(x=categories, y=actuals, name='Факт', marker_color='lightcoral'))

    fig.update_layout(
        title='Сравнение прогноза и факта по категориям расходов',
        xaxis_title='Категории',
        yaxis_title='Сумма',
        barmode='group',
        template='plotly_white',
        height=500
    )

    # Показываем в диалоге
    with ui.dialog() as dialog, ui.card().style("width: 900px"):
        ui.label("📊 График расходов").classes("text-h6")
        ui.plotly(fig).classes("w-full")
        ui.button("Закрыть", on_click=dialog.close)
    dialog.open()

def update_report():
    total_incomes = sum(incomes.values())
    total_forecast = root_expenses.total_forecast()
    total_actual = root_expenses.total_actual()
    balance = total_incomes - total_actual
    total_investments = root_investments.total_amount()
    report_text = f"""
💰 Доходы: {total_incomes:.2f}
📊 Прогноз расходов: {total_forecast:.2f}
📉 Факт расходов: {total_actual:.2f}
📈 Отклонение: {total_forecast - total_actual:+.2f}
💵 Остаток: {balance:.2f}
💼 Инвестиции всего: {total_investments:.2f}
"""
    report_label.set_text(report_text)

def manual_save():
    total_incomes = sum(incomes.values())
    log(f"manual_save: month={current_month}, total_incomes={total_incomes}, forecast={root_expenses.total_forecast()}, actual={root_expenses.total_actual()}", level="INFO")
    save_data(incomes, root_expenses, root_investments, current_month)
    ui.notify("Данные сохранены", type="positive")

def init_data():
    global incomes, root_expenses, root_investments, current_month, available_months
    incomes, root_expenses, root_investments, current_month, available_months = load_data()
    update_month_selector()
    refresh_ui()

def update_month_selector():
    """Обновляет значения в выпадающем списке месяцев"""
    global month_select, available_months, current_month
    if month_select:
        month_select.options = available_months
        if current_month in available_months:
            month_select.value = current_month
        else:
            month_select.value = None

def change_month(month):
    global incomes, root_expenses, root_investments, current_month
    if not month or month == current_month:
        return
    save_data(incomes, root_expenses, root_investments, current_month)
    incomes, root_expenses, root_investments, current_month, _ = load_data(month)
    refresh_ui()
    manual_save()
    ui.notify(f"Загружен месяц {month}", type="info")

def create_new_month():
    with ui.dialog() as dialog, ui.card():
        ui.label("Новый месяц")
        new_month_input = ui.input("Месяц (YYYY-MM)", placeholder="2025-02")
        copy_checkbox = ui.checkbox("Скопировать данные из текущего месяца")
        def confirm():
            # Объявляем global в самом начале
            global available_months, current_month, incomes, root_expenses, root_investments
            new_month = new_month_input.value.strip()
            if not new_month or len(new_month) != 7 or new_month[4] != '-':
                ui.notify("Неверный формат. Используйте ГГГГ-ММ", type="warning")
                return
            if new_month in available_months:
                ui.notify("Месяц уже существует", type="warning")
                return
            # Сохраняем текущий месяц перед созданием нового
            save_data(incomes, root_expenses, root_investments, current_month)
            if copy_checkbox.value:
                new_expenses_dict = root_expenses.to_dict(for_expense=True)
                new_investments_dict = root_investments.to_dict(for_expense=False)
                new_root_exp = CategoryNode("__ROOT_EXPENSES__")
                new_root_inv = CategoryNode("__ROOT_INVESTMENTS__")
                for name, data in new_expenses_dict.items():
                    child = CategoryNode.from_dict(name, data, for_expense=True, parent=new_root_exp)
                    new_root_exp.add_child(child)
                for name, data in new_investments_dict.items():
                    child = CategoryNode.from_dict(name, data, for_expense=False, parent=new_root_inv)
                    new_root_inv.add_child(child)
                save_data(incomes, new_root_exp, new_root_inv, new_month)
            else:
                new_root_exp = CategoryNode("__ROOT_EXPENSES__")
                new_root_inv = CategoryNode("__ROOT_INVESTMENTS__")
                save_data(0.0, new_root_exp, new_root_inv, new_month)
            # Обновляем списки и текущий месяц
            available_months = sorted(available_months + [new_month])
            current_month = new_month
            incomes, root_expenses, root_investments, _, _ = load_data(new_month)
            update_month_selector()
            refresh_ui()
            manual_save()
            dialog.close()
            ui.notify(f"Создан месяц {new_month}", type="positive")
        ui.button("Создать", on_click=confirm)
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()

# ---------- Интерфейс ----------
ui.page_title("Финансовый помощник")
with ui.header(elevated=True).classes("bg-primary text-white"):
    ui.label("💰 Финансовый помощник").classes("text-h4")
# Вторая панель: выбор месяца и создание нового
with ui.row().classes("w-full items-center gap-2 p-2"):
    ui.label("Месяц:").classes("text-subtitle1")
    month_select = ui.select(available_months, value=current_month, on_change=lambda e: change_month(e.value))
    ui.button("➕ Новый месяц", on_click=create_new_month, icon="add").props("outline")

# Панель кнопок с иконками
with ui.row().classes("w-full items-center gap-2 p-2"):
    ui.button("➕ Добавить доход", on_click=show_add_incomes_dialog, icon="add").props("outline")
    ui.button("📋 Доходы", on_click=show_incomes_dialog, icon="list").props("outline")
    ui.button("Добавить расход", on_click=show_add_expense_dialog, icon="shopping_cart").props("outline")
    ui.button("Записать факт", on_click=show_set_actual_dialog, icon="edit_note").props("outline")
    ui.button("Добавить инвестицию", on_click=show_add_investment_dialog, icon="trending_up").props("outline")
    ui.button("Обновить", on_click=refresh_ui, icon="refresh").props("flat")
    ui.button("📊 График", on_click=show_chart_dialog, icon="bar_chart").props("outline")
    ui.button("💾 Сохранить", on_click=manual_save, icon="save").props("outline")
    logging_switch = ui.switch('Логирование', value=True, on_change=lambda e: set_logging_enabled(e.value))
    logging_switch.bind_value_to(globals(), 'logging_enabled') 

# Две колонки
with ui.row().classes("w-full"):
    with ui.column().classes("w-1/2 q-pa-md"):
        ui.label("📋 Расходы").classes("text-h6")
        expenses_container = ui.column().classes("q-ml-md")
    with ui.column().classes("w-1/2 q-pa-md"):
        ui.label("📈 Инвестиции").classes("text-h6")
        investments_container = ui.column().classes("q-ml-md")

# Отчёт
report_label = ui.label().classes("text-subtitle1 q-pa-md")

# Загрузка данных
init_data()

ui.run(host="127.0.0.1", port=8080, title="Финансовый помощник", reload=False)