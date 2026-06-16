# ui/charts_tab.py
from nicegui import ui
import core.state as state
from core.charts import build_chart
from core.utils import get_all_categories

def create_charts_tab(tab_panels, chart_container):
    with tab_panels:
        with ui.tab_panel('Графики'):
            ui.label("📊 Гибкие графики").classes("text-h6 q-pa-md")
            with ui.card().classes("w-full"):
                chart_type = ui.select(["Столбчатая", "Круговая", "Линейный"], value="Столбчатая", label="Тип графика")
                data_source = ui.select(["Расходы", "Инвестиции"], value="Расходы", label="Источник данных")
                
                ui.label("Выберите категории:").classes("text-subtitle2 q-mt-md")
                # Поле ввода с автодополнением (используем все категории)
                category_input = ui.input(
                    placeholder="Начните вводить название категории...",
                    autocomplete=[]
                ).classes("w-full")
                
                selected_container = ui.row().classes("q-mt-sm wrap")
                
                def update_category_input_autocomplete():
                    if data_source.value == "Расходы":
                        cats = get_all_categories(state.root_expenses)
                    else:
                        cats = get_all_categories(state.root_investments)
                    category_input.options = cats
                
                def add_selected_category(input_field, container):
                    text = input_field.value.strip()
                    if not text:
                        ui.notify("Введите название категории", type="warning")
                        return
                    if data_source.value == "Расходы":
                        all_cats = get_all_categories(state.root_expenses)
                    else:
                        all_cats = get_all_categories(state.root_investments)
                    if text not in all_cats:
                        ui.notify(f"Категория '{text}' не найдена", type="warning")
                        return
                    if text in state.selected_categories:
                        ui.notify(f"Категория '{text}' уже выбрана", type="warning")
                        return
                    state.selected_categories.append(text)
                    with container:
                        chip = ui.chip(text, removable=True)
                        chip.on('remove', lambda e, cat=text: remove_selected_category(cat, chip, container))
                    input_field.value = ''
                    ui.notify(f"Добавлена категория: {text}", type="positive")
                
                def remove_selected_category(cat, chip, container):
                    if cat in state.selected_categories:
                        state.selected_categories.remove(cat)
                    chip.delete()
                    ui.notify(f"Удалена категория: {cat}", type="info")
                
                def clear_selected_categories(container):
                    state.selected_categories.clear()
                    container.clear()
                    ui.notify("Все категории удалены", type="info")
                
                with ui.row().classes("q-mt-sm"):
                    ui.button("➕ Добавить", on_click=lambda: add_selected_category(category_input, selected_container), icon="add")
                    ui.button("🗑️ Очистить всё", on_click=lambda: clear_selected_categories(selected_container), icon="delete")
                    ui.button("📊 Построить график", on_click=lambda: build_chart(chart_type, data_source, chart_container), icon="show_chart")
                
                data_source.on('change', update_category_input_autocomplete)
                update_category_input_autocomplete()
            
            # Используем переданный chart_container
            # Он уже создан в webapp.py
            ui.separator()
            ui.label("Подсказка: для круговой диаграммы выберите 'Инвестиции', для линейного графика — 'Инвестиции' и одну категорию.")