# cli.py
import sys
from storage import load_data, save_data
from operations import add_expense_category, set_actual_expense, add_investment_category

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_tree(node, level=0, is_expense=True):
    indent = "  " * level
    # Пропускаем корневые узлы (__ROOT__...)
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

def show_report(income, root_expenses, root_investments):
    print_separator("ФИНАНСОВЫЙ ОТЧЁТ")
    total_forecast = root_expenses.total_forecast()
    total_actual = root_expenses.total_actual()
    balance = income - total_actual
    print(f"💰 Месячный доход: {income:.2f}")
    print(f"📊 Прогнозируемые расходы: {total_forecast:.2f}")
    print(f"📉 Фактические расходы: {total_actual:.2f}")
    print(f"📈 Отклонение прогноза от факта: {total_forecast - total_actual:.2f}")
    print(f"💵 Остаток после расходов: {balance:.2f}")
    print(f"💼 Общая сумма инвестиций: {root_investments.total_amount():.2f}")
    
    print("\n--- Детали по категориям расходов ---")
    for child in root_expenses.children:
        print_tree(child, 0, is_expense=True)
    
    print("\n--- Инвестиции по категориям ---")
    for child in root_investments.children:
        print_tree(child, 0, is_expense=False)

def add_expense_category_interactive(root_expenses):
    path_str = input("Введите путь к категории расходов (через слэш, например Продукты/Мясо): ").strip()
    if not path_str:
        print("❌ Путь не может быть пустым.")
        return
    path = [p.strip() for p in path_str.split('/') if p.strip()]
    if not path:
        print("❌ Некорректный путь.")
        return
    try:
        forecast = float(input("Введите прогнозируемую сумму расходов: "))
    except ValueError:
        print("❌ Некорректная сумма. Используйте число.")
        return
    add_expense_category(path, forecast, root_expenses)
    print(f"✅ Категория {'/'.join(path)} добавлена с прогнозом {forecast:.2f}")

def set_actual_expense_interactive(root_expenses):
    path_str = input("Введите путь к категории (через слэш): ").strip()
    if not path_str:
        print("❌ Путь не может быть пустым.")
        return
    path = [p.strip() for p in path_str.split('/') if p.strip()]
    if not path:
        print("❌ Некорректный путь.")
        return
    try:
        actual = float(input("Введите фактическую сумму расходов: "))
    except ValueError:
        print("❌ Некорректная сумма.")
        return
    try:
        set_actual_expense(path, actual, root_expenses)
        print(f"✅ Фактический расход {actual:.2f} установлен для {'/'.join(path)}")
    except ValueError as e:
        print(f"❌ Ошибка: {e}")

def add_investment_category_interactive(root_investments):
    path_str = input("Введите путь к категории инвестиций (через слэш): ").strip()
    if not path_str:
        print("❌ Путь не может быть пустым.")
        return
    path = [p.strip() for p in path_str.split('/') if p.strip()]
    if not path:
        print("❌ Некорректный путь.")
        return
    try:
        amount = float(input("Введите сумму инвестиций: "))
    except ValueError:
        print("❌ Некорректная сумма.")
        return
    add_investment_category(path, amount, root_investments)
    print(f"✅ Категория {'/'.join(path)} добавлена с инвестициями {amount:.2f}")

def main():
    income, root_expenses, root_investments = load_data()
    print("Добро пожаловать в финансовый помощник!")
    while True:
        print_separator("ГЛАВНОЕ МЕНЮ")
        print("1. Установить/изменить месячный доход")
        print("2. Добавить категорию расходов (с прогнозом)")
        print("3. Записать фактические расходы")
        print("4. Добавить категорию инвестиций")
        print("5. Показать отчёт")
        print("6. Показать дерево расходов")
        print("7. Показать дерево инвестиций")
        print("0. Сохранить и выйти")
        choice = input("Ваш выбор: ").strip()
        
        if choice == '0':
            save_data(income, root_expenses, root_investments)
            print("💾 Данные сохранены. До свидания!")
            break
        elif choice == '1':
            try:
                new_income = float(input("Введите месячный доход: "))
                income = new_income
                print(f"✅ Месячный доход установлен: {income:.2f}")
            except ValueError:
                print("❌ Введите число.")
        elif choice == '2':
            add_expense_category_interactive(root_expenses)
        elif choice == '3':
            set_actual_expense_interactive(root_expenses)
        elif choice == '4':
            add_investment_category_interactive(root_investments)
        elif choice == '5':
            show_report(income, root_expenses, root_investments)
        elif choice == '6':
            print_separator("ДЕРЕВО РАСХОДОВ (прогноз/факт)")
            for child in root_expenses.children:
                print_tree(child, 0, is_expense=True)
        elif choice == '7':
            print_separator("ДЕРЕВО ИНВЕСТИЦИЙ")
            for child in root_investments.children:
                print_tree(child, 0, is_expense=False)
        else:
            print("❌ Неверный выбор, попробуйте снова.")

if __name__ == "__main__":
    main()