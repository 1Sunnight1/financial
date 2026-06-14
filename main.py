# main.py
import sys
from models import CategoryNode
from storage import save_data, load_data
from operations import add_expense_category, set_actual_expense, add_investment_category

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_tree(node, level=0, is_expense=True):
    indent = "  " * level
    if node.name.startswith("__ROOT__"):
        for child in node.children:
            print_tree(child, level, is_expense)
        return
    if is_expense:
        forecast_val = node.total_forecast()
        actual_val = node.total_actual()
        print(f"{indent}📂 {node.name}: прогноз = {forecast_val:.2f}, факт = {actual_val:.2f}, разница = {(forecast_val - actual_val):.2f}")
    else:
        total = node.total_amount()
        print(f"{indent}💰 {node.name}: сумма инвестиций = {total:.2f}")
    for child in node.children:
        print_tree(child, level+1, is_expense)

def report_comparison(root_expenses):
    print_separator("ОТЧЁТ ПО РАСХОДАМ (прогноз vs факт)")
    total_forecast = root_expenses.total_forecast()
    total_actual = root_expenses.total_actual()
    print(f"\n🔹 ОБЩИЙ ИТОГ: прогноз = {total_forecast:.2f}, факт = {total_actual:.2f}, отклонение = {total_forecast - total_actual:.2f}")
    print("\n--- Детали по категориям ---")
    for child in root_expenses.children:
        print_tree(child, 0, is_expense=True)

def test_scenario():
    print_separator("1. ЗАГРУЗКА ДАННЫХ (или создание новых)")
    income, root_exp, root_inv = load_data()
    print(f"📅 Текущий месячный доход: {income:.2f}")
    print("🗂️ Дерево расходов (из загруженных данных):")
    print_tree(root_exp, 0, is_expense=True)
    print("\n💼 Дерево инвестиций (из загруженных данных):")
    print_tree(root_inv, 0, is_expense=False)

    print_separator("2. ДОБАВЛЯЕМ НОВЫЕ КАТЕГОРИИ РАСХОДОВ")
    add_expense_category(["Продукты", "Мясо"], forecast=3000, root=root_exp)
    print("✅ Добавлена категория 'Продукты/Мясо' (прогноз=3000)")
    add_expense_category(["Продукты", "Овощи"], forecast=2000, root=root_exp)
    print("✅ Добавлена категория 'Продукты/Овощи' (прогноз=2000)")
    add_expense_category(["Транспорт", "Бензин"], forecast=5000, root=root_exp)
    print("✅ Добавлена категория 'Транспорт/Бензин' (прогноз=5000)")

    print_separator("3. УСТАНАВЛИВАЕМ ФАКТИЧЕСКИЕ РАСХОДЫ")
    set_actual_expense(["Продукты", "Мясо"], 2800, root=root_exp)
    print("📝 Факт по 'Продукты/Мясо' = 2800")
    set_actual_expense(["Продукты", "Овощи"], 2100, root=root_exp)
    print("📝 Факт по 'Продукты/Овощи' = 2100")
    set_actual_expense(["Транспорт", "Бензин"], 4800, root=root_exp)
    print("📝 Факт по 'Транспорт/Бензин' = 4800")

    print_separator("4. ДОБАВЛЯЕМ КАТЕГОРИИ ИНВЕСТИЦИЙ")
    add_investment_category(["Акции", "Российские"], amount=8000, root=root_inv)
    print("✅ Инвестиции: 'Акции/Российские' = 8000")
    add_investment_category(["Акции", "Зарубежные"], amount=12000, root=root_inv)
    print("✅ Инвестиции: 'Акции/Зарубежные' = 12000")
    add_investment_category(["Недвижимость"], amount=30000, root=root_inv)
    print("✅ Инвестиции: 'Недвижимость' = 30000")

    print_separator("5. ПРОВЕРКА СУММ (ДО СОХРАНЕНИЯ)")
    report_comparison(root_exp)
    print("\n💼 Итог по инвестициям:")
    print_tree(root_inv, 0, is_expense=False)

    print_separator("6. СОХРАНЯЕМ ДАННЫЕ В JSON")
    save_data(income, root_exp, root_inv)
    print(f"💾 Данные сохранены в файл: data/finance_data.json")

    print_separator("7. ЗАГРУЖАЕМ ЗАНОВО (ПРОВЕРКА ВОССТАНОВЛЕНИЯ)")
    del root_exp, root_inv
    loaded_income, loaded_exp, loaded_inv = load_data()
    print(f"📅 Загруженный доход: {loaded_income:.2f}")
    print("🗂️ Восстановленное дерево расходов:")
    print_tree(loaded_exp, 0, is_expense=True)
    print("\n💼 Восстановленное дерево инвестиций:")
    print_tree(loaded_inv, 0, is_expense=False)

    print_separator("8. ФИНАЛЬНАЯ ПРОВЕРКА СУММ ПОСЛЕ ЗАГРУЗКИ")
    total_forecast_loaded = loaded_exp.total_forecast()
    total_actual_loaded = loaded_exp.total_actual()
    total_inv_loaded = loaded_inv.total_amount()
    print(f"🔹 Общий прогноз расходов: {total_forecast_loaded:.2f}")
    print(f"🔹 Общий факт расходов: {total_actual_loaded:.2f}")
    print(f"🔹 Общая сумма инвестиций: {total_inv_loaded:.2f}")
    if total_forecast_loaded == 10000 and total_actual_loaded == 9700 and total_inv_loaded == 50000:
        print("✅ ВСЕ СУММЫ СООТВЕТСТВУЮТ ОЖИДАЕМЫМ! Тест пройден.")
    else:
        print("⚠️ ВНИМАНИЕ: суммы не совпадают с ожидаемыми (прогноз 10000, факт 9700, инвест 50000). Проверьте логи.")

if __name__ == "__main__":
    test_scenario()