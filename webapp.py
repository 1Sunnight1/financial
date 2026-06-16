# webapp.py
from nicegui import ui, app
import matplotlib.pyplot as plt
from storage import load_data, save_data, delete_month, DATA_FILE
from models import CategoryNode
import plotly.graph_objects as go
import copy
from datetime import datetime
from operations import add_daily_expense, add_expense_category, add_investment_category, set_actual_expense
from logger import set_logging_enabled, log, LOGGING_ENABLED
import traceback
from logger import log, log_call

# Глобальные переменные и контейнеры
incomes = {}
root_expenses = None
root_investments = None
current_month = None
available_months = []
expenses_container = None
investments_container = None
report_label = None
month_select = None
selected_categories = [] ## Глобальный список выбранных категорий

# Функции для получения путей категорий (автодополнение)

def get_all_expense_paths():
    """Возвращает список всех путей категорий расходов (например, ['Еда', 'Еда/Мясо', 'Транспорт'])"""
    paths = []
    def walk(node, current):
        for child in node.children:
            new_path = current + [child.name]
            paths.append('/'.join(new_path))
            walk(child, new_path)
    walk(root_expenses, [])
    return sorted(paths)

def get_all_investment_paths():
    """Аналогично для инвестиций"""
    paths = []
    def walk(node, current):
        for child in node.children:
            new_path = current + [child.name]
            paths.append('/'.join(new_path))
            walk(child, new_path)
    walk(root_investments, [])
    return sorted(paths)

def get_flat_categories(node, current_path=''):
    """Рекурсивно собирает все категории (листовые и родительские) с их полными путями"""
    categories = []
    for child in node.children:
        path = current_path + '/' + child.name if current_path else child.name
        categories.append({'name': child.name, 'path': path, 'node': child})
        categories.extend(get_flat_categories(child, path))
    return categories

def get_category_by_path(root_node, path):
    """Возвращает узел категории по пути (например, 'Продукты/Мясо')"""
    parts = path.split('/')
    node = root_node
    for part in parts:
        node = node.find_child(part)
        if node is None:
            return None
    return node

# Функции построения деревьев и обновления UI

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

# Диалоги редактирования и удаления

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

#Диалоги добавления

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
                add_expense_category(path, forecast, root_expenses)
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
            add_investment_category(path, amount, root_investments)
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

# Диалоги для доходов

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

@log_call()
def delete_incomes_transaction(date_str, dialog):
    global incomes
    if date_str in incomes:
        del incomes[date_str]
        refresh_ui()
        manual_save()
        dialog.close()
        ui.notify(f"Доход за {date_str} удалён", type="positive")

# Функции работы с месяцами

def update_month_selector():
    """Обновляет значения в выпадающем списке месяцев"""
    global month_select, available_months, current_month
    if month_select:
        month_select.options = available_months
        if current_month in available_months:
            month_select.value = current_month
        else:
            month_select.value = None

@log_call()
def change_month(month):
    global incomes, root_expenses, root_investments, current_month
    if not month or month == current_month:
        return
    save_data(incomes, root_expenses, root_investments, current_month)
    incomes, root_expenses, root_investments, current_month, _ = load_data(month)
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
            # Объявляем global в самом начале
            global available_months, current_month, incomes, root_expenses, root_investments
            new_month = new_month_input.value  # уже строка в формате YYYY-MM
            if not new_month or len(new_month) != 7 or new_month[4] != '-':
                ui.notify("Неверный формат. Используйте ГГГГ-ММ", type="warning")
                return
            if new_month in available_months:
                ui.notify("Месяц уже существует", type="warning")
                return
            # Сохраняем текущий месяц перед созданием нового
            save_data(incomes, root_expenses, root_investments, current_month)
            if copy_checkbox.value:
                # Копируем детей корня расходов
                new_expenses_dict = {}
                for child in root_expenses.children:
                    new_expenses_dict[child.name] = child.to_dict(for_expense=True)
                new_investments_dict = {}
                for child in root_investments.children:
                    new_investments_dict[child.name] = child.to_dict(for_expense=False)
                
                new_root_exp = CategoryNode("__ROOT_EXPENSES__")
                new_root_inv = CategoryNode("__ROOT_INVESTMENTS__")
                for name, data in new_expenses_dict.items():
                    child_node = CategoryNode.from_dict(name, data, for_expense=True, parent=new_root_exp)
                    new_root_exp.add_child(child_node)
                for name, data in new_investments_dict.items():
                    child_node = CategoryNode.from_dict(name, data, for_expense=False, parent=new_root_inv)
                    new_root_inv.add_child(child_node)
                save_data(incomes, new_root_exp, new_root_inv, new_month)
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

@log_call()
def delete_current_month():
    global incomes, root_expenses, root_investments, current_month, available_months
    if not current_month:
        ui.notify("Нет текущего месяца для удаления", type="warning")
        return
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Удалить месяц {current_month}?")
        ui.label("Все данные за этот месяц будут удалены.").classes("text-caption")
        with ui.row():
            def confirm(month=current_month):
                success = delete_month(month)
                if success:
                    global incomes, root_expenses, root_investments, current_month, available_months
                    incomes, root_expenses, root_investments, current_month, available_months = load_data()
                    update_month_selector()
                    refresh_ui()
                    ui.notify(f"Месяц {month} удалён", type="positive")
                else:
                    ui.notify("Не удалось удалить месяц", type="negative")
                dialog.close()
            ui.button("Удалить", on_click=confirm).props("color=negative")
            ui.button("Отмена", on_click=dialog.close)
    dialog.open()

# Функции отчёта и сохранения

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

@log_call()
def manual_save():
    total_incomes = sum(incomes.values())
    log(f"manual_save: month={current_month}, total_incomes={total_incomes}, forecast={root_expenses.total_forecast()}, actual={root_expenses.total_actual()}", level="INFO")
    save_data(incomes, root_expenses, root_investments, current_month)
    ui.notify("Данные сохранены", type="positive")

@log_call()
def init_data():
    global incomes, root_expenses, root_investments, current_month, available_months
    incomes, root_expenses, root_investments, current_month, available_months = load_data()
    log(f"init_data: загружено {len(root_expenses.children)} категорий расходов, {len(root_investments.children)} категорий инвестиций", level="DEBUG")
    update_month_selector()
    refresh_ui()


# Функции для графиков
def get_all_leaf_categories(node, parent_path=""):
    log(f"get_all_leaf_categories: node={node.name if node else 'None'}, parent_path={parent_path}, children={len(node.children) if node else 0}", level="DEBUG")
    """Возвращает список путей всех листовых категорий (без детей)"""
    paths = []
    for child in node.children:
        current_path = f"{parent_path}/{child.name}" if parent_path else child.name
        if not child.children:
            log(f"get_all_leaf_categories: добавляем листовую категорию: {current_path}", level="DEBUG")
            paths.append(current_path)
        else:
            paths.extend(get_all_leaf_categories(child, current_path))
    return paths

def build_chart(chart_type, data_source, chart_container):
    selected = selected_categories
    if not selected:
        ui.notify("Выберите хотя бы одну категорию", type="warning")
        return
    if chart_type.value == "Столбчатая" and data_source.value == "Расходы":
        forecasts = []
        actuals = []
        for cat_path in selected:
            parts = cat_path.split('/')
            node = root_expenses
            for part in parts:
                node = node.find_child(part) if node else None
            if node:
                forecasts.append(node.total_forecast())
                actuals.append(node.total_actual())
            else:
                forecasts.append(0)
                actuals.append(0)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=selected, y=forecasts, name='Прогноз', marker_color='skyblue'))
        fig.add_trace(go.Bar(x=selected, y=actuals, name='Факт', marker_color='lightcoral'))
        fig.update_layout(barmode='group', title="Сравнение прогноза и факта")
        log(f"build_chart: строим график для выбранных категорий: {selected}", level="DEBUG")
        chart_container.clear()
        with chart_container:
            ui.plotly(fig).classes("w-full h-96")
    elif chart_type.value == "Круговая" and data_source.value == "Инвестиции":
        amounts = []
        for cat_path in selected:
            parts = cat_path.split('/')
            node = root_investments
            for part in parts:
                node = node.find_child(part) if node else None
            amounts.append(node.total_amount() if node else 0)
        fig = go.Figure(data=[go.Pie(labels=selected, values=amounts, hole=.3)])
        fig.update_layout(title="Распределение инвестиций")
        chart_container.clear()
        with chart_container:
            ui.plotly(fig).classes("w-full h-96")
    elif chart_type.value == "Линейный" and data_source.value == "Инвестиции":
        if len(selected) != 1:
            ui.notify("Для линейного графика выберите ровно одну категорию", type="warning")
            return
        category_path = selected[0]
        parts = category_path.split('/')
        import json, os
        months = []
        amounts = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for month in sorted(data.get("months", {}).keys()):
                month_data = data["months"][month]
                inv_data = month_data.get("investments", {})
                def find_in_dict(d, parts):
                    if not parts:
                        return None
                    part = parts[0]
                    if part in d:
                        if len(parts) == 1:
                            return d[part]
                        else:
                            return find_in_dict(d[part].get("children", {}), parts[1:])
                    return None
                found = find_in_dict(inv_data, parts)
                if found and "amount" in found:
                    amount = found["amount"]
                elif found and "children" in found:
                    def sum_children(node_dict):
                        s = node_dict.get("amount", 0)
                        for child in node_dict.get("children", {}).values():
                            s += sum_children(child)
                        return s
                    amount = sum_children(found)
                else:
                    amount = 0
                months.append(month)
                amounts.append(amount)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=amounts, mode='lines+markers', name=category_path))
        fig.update_layout(title=f"Динамика инвестиций: {category_path}")
        chart_container.clear()
        with chart_container:
            ui.plotly(fig).classes("w-full h-96")
    else:
        ui.notify(f"Комбинация {chart_type.value} + {data_source.value} не реализована", type="warning")

def init_categories(data_source, category_select):
    log(f"init_categories: data_source.value={data_source.value}, category_select={category_select}", level="DEBUG")
    cats = []
    if data_source.value == "Расходы":
        cats = get_all_leaf_categories(root_expenses)
    else:
        cats = get_all_leaf_categories(root_investments)
    log(f"init_categories: найдено категорий: {len(cats)}, первые 5: {cats[:5]}", level="DEBUG")
    log(f"init_categories: устанавливаем options = {cats}", level="DEBUG")
    category_select.options = cats
    category_select.value = cats  

# Вспомогательные функции для гибких графиков 

def prepare_expense_data_for_month(month_data, category_node, data_type='actual'):
    """
    Для заданного узла категории и месяца возвращает сумму прогноза или факта.
    month_data - данные за месяц (словарь из load_data, но мы будем загружать нужные месяцы по мере необходимости)
    """
    # Эта функция будет использоваться для линейных графиков по месяцам
    pass  # пока заглушка, реализуем позже

# Интерфейс 
ui.page_title("Финансовый помощник")

with ui.header(elevated=True).classes("bg-primary text-white"):
    ui.label("💰 Финансовый помощник").classes("text-h4")

## Горизонтальные вкладки
tabs = ui.tabs().classes('w-full')
with tabs:
    ui.tab('Главная', icon='home')
    ui.tab('Графики', icon='bar_chart')
    ui.tab('Настройки', icon='settings')

## Панели вкладок
tab_panels = ui.tab_panels(tabs, value='Главная').classes('w-full')

## Вкладки
with tab_panels:
    with ui.tab_panel('Главная'):
        ### Строка выбора месяца
        with ui.row().classes("w-full items-center gap-2 p-2"):
            ui.label("Месяц:").classes("text-subtitle1")
            month_select = ui.select(available_months, value=current_month, on_change=lambda e: change_month(e.value))
            ui.button("➕ Новый месяц", on_click=create_new_month, icon="add").props("outline")
            ui.button("🗑️ Удалить месяц", on_click=delete_current_month, icon="delete").props("outline").props("color=negative")

        ### Панель кнопок действий
        with ui.row().classes("w-full items-center gap-2 p-2"):
            ui.button("➕ Добавить доход", on_click=show_add_incomes_dialog, icon="add").props("outline")
            ui.button("📋 Доходы", on_click=show_incomes_dialog, icon="list").props("outline")
            ui.button("Добавить расход", on_click=show_add_expense_dialog, icon="shopping_cart").props("outline")
            ui.button("Записать факт", on_click=show_set_actual_dialog, icon="edit_note").props("outline")
            ui.button("Добавить инвестицию", on_click=show_add_investment_dialog, icon="trending_up").props("outline")
            ui.button("Обновить", on_click=refresh_ui, icon="refresh").props("flat")
            ui.button("💾 Сохранить", on_click=manual_save, icon="save").props("outline")

        ### Две колонки: расходы и инвестиции
        with ui.row().classes("w-full"):
            with ui.column().classes("w-1/2 q-pa-md"):
                ui.label("📋 Расходы").classes("text-h6")
                expenses_container = ui.column().classes("q-ml-md")
            with ui.column().classes("w-1/2 q-pa-md"):
                ui.label("📈 Инвестиции").classes("text-h6")
                investments_container = ui.column().classes("q-ml-md")

        ### Отчёт
        report_label = ui.label().classes("text-subtitle1 q-pa-md")

        ### Инициализация данных (вызывается один раз)
        init_data()
        
    with ui.tab_panel('Графики'):
        ui.label("📊 Гибкие графики").classes("text-h6 q-pa-md")
        
        # Панель управления
        with ui.card().classes("w-full"):
            chart_type = ui.select(["Столбчатая", "Круговая", "Линейный"], value="Столбчатая", label="Тип графика")
            data_source = ui.select(["Расходы", "Инвестиции"], value="Расходы", label="Источник данных")
            
            ui.label("Выберите категории (введите название и нажмите «Добавить»):").classes("text-subtitle2 q-mt-md")
            
            # Поле ввода с автодополнением
            category_input = ui.input(
                placeholder="Начните вводить название категории...",
                autocomplete=[]
            ).classes("w-full")
            
            # Контейнер для выбранных категорий (чипы)
            selected_container = ui.row().classes("q-mt-sm wrap")
            
            # Кнопки управления
            with ui.row().classes("q-mt-sm"):
                ui.button("➕ Добавить категорию", on_click=lambda: add_selected_category(category_input, selected_container), icon="add")
                ui.button("🗑️ Очистить все", on_click=lambda: clear_selected_categories(selected_container), icon="delete")
                ui.button("Построить график", on_click=lambda: build_chart(chart_type, data_source, chart_container), icon="show_chart")
            
            # Функция обновления списка автодополнения и выбранных категорий
            def update_category_input_autocomplete():
                if data_source.value == "Расходы":
                    cats = get_all_leaf_categories(root_expenses)
                else:
                    cats = get_all_leaf_categories(root_investments)
                category_input.options = cats
            
            def add_selected_category(input_field, container):
                text = input_field.value.strip()
                if not text:
                    ui.notify("Введите название категории", type="warning")
                    return
                # Проверяем, существует ли такая категория
                if data_source.value == "Расходы":
                    all_cats = get_all_leaf_categories(root_expenses)
                else:
                    all_cats = get_all_leaf_categories(root_investments)
                if text not in all_cats:
                    ui.notify(f"Категория '{text}' не найдена", type="warning")
                    return
                if text in selected_categories:
                    ui.notify(f"Категория '{text}' уже выбрана", type="warning")
                    return
                selected_categories.append(text)
                # Добавляем чип
                with container:
                    chip = ui.chip(text, removable=True)
                    chip.on('remove', lambda e, cat=text: remove_selected_category(cat, chip, container))
                input_field.value = ''
                ui.notify(f"Добавлена категория: {text}", type="positive")
                log(f"Добавлена категория для графика: {text}", level="DEBUG")
            
            def remove_selected_category(cat, chip, container):
                if cat in selected_categories:
                    selected_categories.remove(cat)
                chip.delete()
                ui.notify(f"Удалена категория: {cat}", type="info")
                log(f"Удалена категория из графика: {cat}", level="DEBUG")
            
            def clear_selected_categories(container):
                global selected_categories
                selected_categories.clear()
                container.clear()
                ui.notify("Все категории удалены", type="info")
                log("Очищен список категорий для графика", level="DEBUG")
            
            # Обновляем автодополнение при смене источника данных
            data_source.on('change', lambda: update_category_input_autocomplete())
            # Инициализация при загрузке
            update_category_input_autocomplete()
        
        # Контейнер для графика
        chart_container = ui.column().classes("w-full")
        ui.separator()
        ui.label("Подсказка: для круговой диаграммы выберите 'Инвестиции', для линейного графика — 'Инвестиции' и одну категорию.")    
    
    with ui.tab_panel('Настройки'):
        ui.label("⚙️ Настройки приложения").classes("text-h6 q-pa-md")
        from logger import LOGGING_ENABLED, set_logging_enabled
        ui.switch('Логирование (запись в файл)', value=LOGGING_ENABLED, on_change=lambda e: set_logging_enabled(e.value))
        ui.label("Логи сохраняются в папке logs/").classes("text-caption")

# Запуск
ui.run(host="127.0.0.1", port=8080, title="Финансовый помощник", reload=False)