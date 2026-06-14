# operations.py
from models import CategoryNode

def add_expense_category(path_parts, forecast, root):
    node = root
    for part in path_parts:
        child = node.find_child(part)
        if child is None:
            child = CategoryNode(part, parent=node)
            node.add_child(child)
        node = child
    node.forecast = forecast
    return node

def set_actual_expense(path_parts, actual, root):
    node = root
    for part in path_parts:
        node = node.find_child(part)
        if node is None:
            raise ValueError(f"Категория {part} не найдена в {'/'.join(path_parts)}")
    node.actual = actual

def add_investment_category(path_parts, amount, root):
    node = root
    for part in path_parts:
        child = node.find_child(part)
        if child is None:
            child = CategoryNode(part, parent=node)
            node.add_child(child)
        node = child
    node.amount = amount
    return node

def add_daily_expense(path_parts, date, amount, root):
    """Добавляет ежедневную запись расхода. date в формате 'YYYY-MM-DD'"""
    node = root
    for part in path_parts:
        node = node.find_child(part)
        if node is None:
            raise ValueError(f"Категория {part} не найдена в {'/'.join(path_parts)}")
    # Если узел - листовой или любой, добавляем запись
    if date in node.daily:
        node.daily[date] += amount
    else:
        node.daily[date] = amount
    return node

# Добавление дохода
def add_income(incomes_dict, date, amount):
    if date in incomes_dict:
        incomes_dict[date] += amount
    else:
        incomes_dict[date] = amount
    return incomes_dict

def delete_income(incomes_dict, date):
    if date in incomes_dict:
        del incomes_dict[date]
    return incomes_dict

def total_income(incomes_dict):
    return sum(incomes_dict.values())