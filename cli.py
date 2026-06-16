#!/usr/bin/env python3
# cli.py - консольный интерфейс финансового помощника

import sys
from datetime import datetime
import core.state as state
from core.month_operations import change_month, create_new_month, delete_current_month, manual_save, update_month_selector
from core.tree_builder import refresh_ui  # не используем для вывода, но используем для обновления состояния
from core.report import update_report      # не используем, но можем взять логику
from core.utils import get_all_categories, get_all_leaf_categories
from operations import add_expense_category, add_investment_category, add_daily_expense
from storage import load_data, save_data
from models import CategoryNode
from logger import log, LOGGING_ENABLED

# ----------------------------------------------------------------------
# Вспомогательные функции для консольного вывода
# ----------------------------------------------------------------------

def print_separator(title=None):
    print("=" * 60)
    if title:
        print(title)
        print("=" * 60)

def print_tree(node, level=0, is_expense=True):
    """Рекурсивно выводит дерево категорий в консоль"""
    for child in node.children:
        indent = "  " * level
        if is_expense:
            forecast_val = child.total_forecast()
            actual_val = child.total_actual()
            diff = forecast_val - actual_val
            print(f"{indent}- {child.name}: прогноз {forecast_val:.2f}, факт {actual_val:.2f} (разница {diff:+.2f})")
        else:
            total = child.total_amount()
            print(f"{indent}- {child.name}: {total:.2f}")
        print_tree(child, level + 1, is_expense)

def show_report():
    """Выводит финансовый отчёт в консоль"""
    total_incomes = sum(state.incomes.values())
    total_forecast = state.root_expenses.total_forecast()
    total_actual = state.root_expenses.total_actual()
    balance = total_incomes - total_actual
    total_investments = state.root_investments.total_amount()
    print_separator("ФИНАНСОВЫЙ ОТЧЁТ")
    print(f"Доходы: {total_incomes:.2f}")
    print(f"Прогноз расходов: {total_forecast:.2f}")
    print(f"Факт расходов: {total_actual:.2f}")
    print(f"Отклонение: {total_forecast - total_actual:+.2f}")
    print(f"Остаток: {balance:.2f}")
    print(f"Инвестиции всего: {total_investments:.2f}")

def show_expenses_tree():
    print_separator("ДЕРЕВО РАСХОДОВ")
    if not state.root_expenses.children:
        print("Нет категорий расходов.")
    else:
        print_tree(state.root_expenses, is_expense=True)

def show_investments_tree():
    print_separator("ДЕРЕВО ИНВЕСТИЦИЙ")
    if not state.root_investments.children:
        print("Нет категорий инвестиций.")
    else:
        print_tree(state.root_investments, is_expense=False)

def input_date(prompt="Дата (ГГГГ-ММ-ДД): "):
    while True:
        s = input(prompt).strip()
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            print("Неверный формат. Используйте ГГГГ-ММ-ДД.")

def input_float(prompt):
    while True:
        s = input(prompt).strip()
        try:
            return float(s)
        except ValueError:
            print("Введите число.")

def input_path(prompt="Путь (через слэш): "):
    while True:
        s = input(prompt).strip()
        if s:
            return [p.strip() for p in s.split('/') if p.strip()]
        print("Путь не может быть пустым.")

# ----------------------------------------------------------------------
# Действия пользователя
# ----------------------------------------------------------------------

def action_add_income():
    print_separator("ДОБАВЛЕНИЕ ДОХОДА")
    date_str = input_date()
    amount = input_float("Сумма: ")
    if date_str in state.incomes:
        state.incomes[date_str] += amount
    else:
        state.incomes[date_str] = amount
    manual_save()
    print(f"Доход {amount} за {date_str} добавлен.")

def action_add_expense():
    print_separator("ДОБАВЛЕНИЕ КАТЕГОРИИ РАСХОДОВ")
    path = input_path("Путь (через слэш): ")
    forecast = input_float("Прогноз: ")
    add_expense_category(path, forecast, state.root_expenses)
    manual_save()
    print(f"Категория {'/'.join(path)} добавлена с прогнозом {forecast:.2f}.")

def action_set_actual():
    print_separator("ЗАПИСЬ ФАКТИЧЕСКОГО РАСХОДА")
    path = input_path("Путь к категории: ")
    date_str = input_date()
    amount = input_float("Сумма: ")
    try:
        add_daily_expense(path, date_str, amount, state.root_expenses)
        manual_save()
        print(f"Запись {amount} за {date_str} добавлена.")
    except ValueError as e:
        print(f"Ошибка: {e}")

def action_add_investment():
    print_separator("ДОБАВЛЕНИЕ ИНВЕСТИЦИИ")
    path = input_path("Путь (через слэш): ")
    amount = input_float("Сумма: ")
    add_investment_category(path, amount, state.root_investments)
    manual_save()
    print(f"Инвестиция {'/'.join(path)} добавлена с суммой {amount:.2f}.")

def action_change_month():
    print_separator("ПЕРЕКЛЮЧЕНИЕ МЕСЯЦА")
    print(f"Текущий месяц: {state.current_month}")
    print(f"Доступные месяцы: {', '.join(state.available_months) if state.available_months else 'нет'}")
    new_month = input("Введите месяц (ГГГГ-ММ) или оставьте пустым для отмены: ").strip()
    if not new_month:
        return
    if new_month not in state.available_months:
        print(f"Месяц {new_month} не найден.")
        return
    change_month(new_month)

def action_create_month():
    print_separator("СОЗДАНИЕ НОВОГО МЕСЯЦА")
    new_month = input("Введите новый месяц (ГГГГ-ММ): ").strip()
    if not new_month or len(new_month) != 7 or new_month[4] != '-':
        print("Неверный формат.")
        return
    if new_month in state.available_months:
        print("Такой месяц уже существует.")
        return
    # Упрощённо: создаём новый месяц без копирования (или с копированием? запросим)
    copy_choice = input("Скопировать данные из текущего месяца? (y/n): ").strip().lower()
    copy_data = copy_choice == 'y'
    # Используем функцию create_new_month, но она вызывает диалог; перепишем логику здесь
    # Поскольку у нас есть функции, мы можем сделать вручную:
    save_data(state.incomes, state.root_expenses, state.root_investments, state.current_month)
    if copy_data:
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
        new_root_exp = CategoryNode("__ROOT_EXPENSES__")
        new_root_inv = CategoryNode("__ROOT_INVESTMENTS__")
        save_data({}, new_root_exp, new_root_inv, new_month)
    # Обновляем состояние
    incomes, root_expenses, root_investments, current_month, available_months = load_data(new_month)
    state.incomes, state.root_expenses, state.root_investments, state.current_month, state.available_months = incomes, root_expenses, root_investments, current_month, available_months
    update_month_selector()
    print(f"Месяц {new_month} создан.")

def action_delete_month():
    print_separator("УДАЛЕНИЕ МЕСЯЦА")
    if not state.current_month:
        print("Нет текущего месяца.")
        return
    print(f"Текущий месяц: {state.current_month}")
    confirm = input(f"Удалить месяц {state.current_month}? (y/n): ").strip().lower()
    if confirm == 'y':
        from core.month_operations import delete_month_internal
        success = delete_month_internal(state.current_month)
        if success:
            print("Месяц удалён.")
        else:
            print("Не удалось удалить месяц.")
            
def action_exit():
    print("Сохранение данных...")
    manual_save()
    print("До свидания!")
    sys.exit(0)

# ----------------------------------------------------------------------
# Главное меню
# ----------------------------------------------------------------------

def main_menu():
    # Загружаем данные
    incomes, root_expenses, root_investments, current_month, available_months = load_data()
    state.incomes, state.root_expenses, state.root_investments, state.current_month, state.available_months = incomes, root_expenses, root_investments, current_month, available_months
    update_month_selector()
    # Основной цикл
    while True:
        print_separator("ГЛАВНОЕ МЕНЮ")
        print(f"Текущий месяц: {state.current_month}")
        print("1. Показать отчёт")
        print("2. Добавить доход")
        print("3. Добавить категорию расходов (с прогнозом)")
        print("4. Записать фактический расход")
        print("5. Добавить инвестицию")
        print("6. Показать дерево расходов")
        print("7. Показать дерево инвестиций")
        print("8. Переключить месяц")
        print("9. Создать новый месяц")
        print("10. Удалить текущий месяц")
        print("0. Выйти")
        choice = input("Ваш выбор: ").strip()
        if choice == "0":
            action_exit()
        elif choice == "1":
            show_report()
        elif choice == "2":
            action_add_income()
        elif choice == "3":
            action_add_expense()
        elif choice == "4":
            action_set_actual()
        elif choice == "5":
            action_add_investment()
        elif choice == "6":
            show_expenses_tree()
        elif choice == "7":
            show_investments_tree()
        elif choice == "8":
            action_change_month()
        elif choice == "9":
            action_create_month()
        elif choice == "10":
            action_delete_month()
        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main_menu()