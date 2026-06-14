# webapp.py
from nicegui import ui, app
import matplotlib.pyplot as plt
from nicegui import ui, app
from storage import load_data, save_data
from operations import add_expense_category, add_investment_category, set_actual_expense
from models import CategoryNode
import plotly.graph_objects as go

# ---------- Глобальное состояние ----------
income = 0.0
root_expenses = None
root_investments = None

# Контейнеры
expenses_container = None
investments_container = None
report_label = None

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
            dialog.close()
            ui.notify(f"Категория '{category.name}' удалена", type="warning")
        ui.button("Удалить", on_click=delete).props("color=negative")
        ui.button("Отмена", on_click=dialog.close)
    dialog.open()

def show_quick_edit_dialog(category, is_expense=True):
    """Быстрое редактирование: для расходов - прогноз и факт, для инвестиций - сумма"""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Редактирование: {category.name}")
        if is_expense:
            forecast_val = category.forecast if category.forecast is not None else 0.0
            actual_val = category.actual if category.actual is not None else 0.0
            forecast_input = ui.number("Прогноз", value=forecast_val, step=100)
            actual_input = ui.number("Факт", value=actual_val, step=100)
            def save():
                category.forecast = forecast_input.value
                category.actual = actual_input.value
                refresh_ui()
                dialog.close()
                ui.notify("Данные обновлены", type="positive")
        else:
            amount_input = ui.number("Сумма", value=category.amount, step=1000)
            def save():
                category.amount = amount_input.value
                refresh_ui()
                dialog.close()
                ui.notify("Сумма обновлена", type="positive")
        ui.button("Сохранить", on_click=save)
        ui.button("Отмена", on_click=dialog.close)
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
            dialog.close()
            ui.notify(f"✅ Инвестиция '{path_str}' добавлена", type="positive")
        ui.button("Добавить", on_click=add, icon="add")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

def show_set_actual_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("📝 Записать фактический расход")
        path_input = ui.input("Путь к категории", placeholder="Еда/Рестораны")
        actual_input = ui.number("Сумма", value=0.0, step=100)
        def set_act():
            path_str = path_input.value.strip()
            if not path_str:
                ui.notify("Введите путь", type="warning")
                return
            path = [p.strip() for p in path_str.split('/') if p.strip()]
            actual = actual_input.value
            try:
                set_actual_expense(path, actual, root_expenses)
                refresh_ui()
                dialog.close()
                ui.notify(f"✅ Факт {actual} для '{path_str}' установлен", type="positive")
            except ValueError as e:
                ui.notify(str(e), type="negative")
        ui.button("Записать", on_click=set_act, icon="edit")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

def show_set_income_dialog():
    with ui.dialog() as dialog, ui.card():
        ui.label("💰 Месячный доход")
        income_input = ui.number("Доход", value=income, step=1000)
        def set_inc():
            global income
            income = income_input.value
            refresh_ui()
            dialog.close()
            ui.notify(f"Доход установлен: {income:.2f}", type="positive")
        ui.button("Сохранить", on_click=set_inc, icon="save")
        ui.button("Отмена", on_click=dialog.close, icon="close")
    dialog.open()

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
    total_forecast = root_expenses.total_forecast()
    total_actual = root_expenses.total_actual()
    balance = income - total_actual
    total_investments = root_investments.total_amount()
    report_text = f"""
💰 Доход: {income:.2f}
📊 Прогноз расходов: {total_forecast:.2f}
📉 Факт расходов: {total_actual:.2f}
📈 Отклонение: {total_forecast - total_actual:+.2f}
💵 Остаток: {balance:.2f}
💼 Инвестиции всего: {total_investments:.2f}
"""
    report_label.set_text(report_text)

def init_data():
    global income, root_expenses, root_investments
    income, root_expenses, root_investments = load_data()
    refresh_ui()

@app.on_shutdown
def shutdown():
    save_data(income, root_expenses, root_investments)
    print("Данные сохранены.")

# ---------- Интерфейс ----------
ui.page_title("Финансовый помощник")
with ui.header(elevated=True).classes("bg-primary text-white"):
    ui.label("💰 Финансовый помощник").classes("text-h4")

# Панель кнопок с иконками
with ui.row().classes("w-full items-center gap-2 p-2"):
    ui.button("Установить доход", on_click=show_set_income_dialog, icon="attach_money").props("outline")
    ui.button("Добавить расход", on_click=show_add_expense_dialog, icon="shopping_cart").props("outline")
    ui.button("Записать факт", on_click=show_set_actual_dialog, icon="edit_note").props("outline")
    ui.button("Добавить инвестицию", on_click=show_add_investment_dialog, icon="trending_up").props("outline")
    ui.button("Обновить", on_click=refresh_ui, icon="refresh").props("flat")
    ui.button("📊 График", on_click=show_chart_dialog, icon="bar_chart").props("outline")

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