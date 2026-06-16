# core/charts.py
from nicegui import ui
import plotly.graph_objects as go
import json, os
import core.state as state
from core.utils import get_all_categories
from storage import DATA_FILE
from logger import log

def build_chart(chart_type, data_source, chart_container):
    selected = state.selected_categories
    if not selected:
        ui.notify("Выберите хотя бы одну категорию", type="warning")
        return

    if chart_type.value == "Столбчатая" and data_source.value == "Расходы":
        forecasts = []
        actuals = []
        for cat_path in selected:
            parts = cat_path.split('/')
            node = state.root_expenses
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
        log(f"build_chart: строим столбчатую диаграмму для категорий: {selected}", level="DEBUG")
        chart_container.clear()
        with chart_container:
            ui.plotly(fig).classes("w-full h-96")

    elif chart_type.value == "Круговая" and data_source.value == "Инвестиции":
        amounts = []
        for cat_path in selected:
            parts = cat_path.split('/')
            node = state.root_investments
            for part in parts:
                node = node.find_child(part) if node else None
            amounts.append(node.total_amount() if node else 0)
        fig = go.Figure(data=[go.Pie(labels=selected, values=amounts, hole=.3)])
        fig.update_layout(title="Распределение инвестиций")
        log(f"build_chart: строим круговую диаграмму для категорий: {selected}", level="DEBUG")
        chart_container.clear()
        with chart_container:
            ui.plotly(fig).classes("w-full h-96")

    elif chart_type.value == "Линейный" and data_source.value == "Инвестиции":
        if len(selected) != 1:
            ui.notify("Для линейного графика выберите ровно одну категорию", type="warning")
            return
        category_path = selected[0]
        parts = category_path.split('/')
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
        log(f"build_chart: строим линейный график для категории: {category_path}", level="DEBUG")
        chart_container.clear()
        with chart_container:
            ui.plotly(fig).classes("w-full h-96")

    else:
        ui.notify(f"Комбинация {chart_type.value} + {data_source.value} не реализована", type="warning")