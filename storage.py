# storage.py 

import json
import os
from datetime import datetime
from models import CategoryNode
from logger import log

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "finance_data.json")

def get_current_month():
    return datetime.now().strftime("%Y-%m")

def save_data(income, root_expenses, root_investments, month=None):
    # NOTE: параметр income пока оставлен для совместимости, но будет заменён на incomes_dict
    if month is None:
        month = get_current_month()
    os.makedirs(DATA_DIR, exist_ok=True)

    # Загружаем существующие данные (если есть)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                else:
                    data = {"months": {}, "current_month": month}
        except json.JSONDecodeError:
            data = {"months": {}, "current_month": month}
    else:
        data = {"months": {}, "current_month": month}

    # Сохраняем деревья расходов и инвестиций
    expenses_dict = {}
    for child in root_expenses.children:
        expenses_dict[child.name] = child.to_dict(for_expense=True)
    investments_dict = {}
    for child in root_investments.children:
        investments_dict[child.name] = child.to_dict(for_expense=False)

    # Подготовка данных за указанный месяц
    if month not in data["months"]:
        data["months"][month] = {}
    month_data = data["months"][month]
    # Сохраняем incomes (если пришёл словарь) или совместимость (если income - число)
    if isinstance(income, dict):
        month_data["incomes"] = income
    elif isinstance(income, (int, float)):
        # Старый формат, конвертируем в транзакцию на первое число месяца
        first_day = f"{month}-01"
        month_data["incomes"] = {first_day: income}
    else:
        # Если income не задан, оставляем как есть или пустой словарь
        if "incomes" not in month_data:
            month_data["incomes"] = {}
    month_data["expenses"] = expenses_dict
    month_data["investments"] = investments_dict
    data["current_month"] = month

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log(f"save_data: данные записаны для месяца {month}", level="INFO")

def load_data(month=None):
    root_exp = CategoryNode("__ROOT_EXPENSES__")
    root_inv = CategoryNode("__ROOT_INVESTMENTS__")

    if not os.path.exists(DATA_FILE):
        # Возвращаем пустой словарь incomes, месяц и пустые деревья
        return {}, root_exp, root_inv, get_current_month(), []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}, root_exp, root_inv, get_current_month(), []
            data = json.loads(content)
    except json.JSONDecodeError:
        return {}, root_exp, root_inv, get_current_month(), []

    # Конвертация старого формата (без months) -> новый
    if "months" not in data:
        # Старый формат: поле monthly_income, expenses, investments
        old_income = data.get("monthly_income", 0.0)
        old_expenses = data.get("expenses", {})
        old_investments = data.get("investments", {})
        current_month = get_current_month()
        data = {"months": {}, "current_month": current_month}
        # Создаём транзакцию дохода на первое число текущего месяца
        first_day = f"{current_month}-01"
        data["months"][current_month] = {
            "incomes": {first_day: old_income},
            "expenses": old_expenses,
            "investments": old_investments
        }
        # Перезаписываем файл в новом формате
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    if month is None:
        month = data.get("current_month", get_current_month())

    available_months = sorted(data.get("months", {}).keys())
    if month not in data["months"]:
        # Возвращаем пустой словарь incomes, пустые деревья
        return {}, root_exp, root_inv, month, available_months

    month_data = data["months"][month]
    # Извлекаем incomes (словарь дата->сумма)
    incomes = month_data.get("incomes", {})
    # Если есть старое поле income (число) и нет incomes, конвертируем
    if "income" in month_data and not incomes:
        first_day = f"{month}-01"
        incomes = {first_day: month_data["income"]}
        # и сохраняем обратно (не обязательно, но можно)
        month_data["incomes"] = incomes

    # Восстанавливаем деревья расходов и инвестиций
    exp_data = month_data.get("expenses", {})
    for child_name, child_data in exp_data.items():
        if isinstance(child_data, dict):
            child_node = CategoryNode.from_dict(child_name, child_data, for_expense=True, parent=root_exp)
            root_exp.add_child(child_node)
    inv_data = month_data.get("investments", {})
    for child_name, child_data in inv_data.items():
        if isinstance(child_data, dict):
            child_node = CategoryNode.from_dict(child_name, child_data, for_expense=False, parent=root_inv)
            root_inv.add_child(child_node)

    return incomes, root_exp, root_inv, month, available_months

def delete_month(month):
    """Удаляет указанный месяц из файла данных"""
    log(f"delete_month: пытаемся удалить месяц {month}", level="DEBUG")
    if not os.path.exists(DATA_FILE):
        log("delete_month: файл данных не существует", level="DEBUG")
        return False
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        months = list(data.get("months", {}).keys())
        log(f"delete_month: загружены месяцы: {months}", level="DEBUG")
        if "months" in data and month in data["months"]:
            del data["months"][month]
            log(f"delete_month: месяц {month} удалён из словаря", level="DEBUG")
            # Если удалён текущий месяц, устанавливаем текущим первый доступный или None
            if data.get("current_month") == month:
                new_months = sorted(data["months"].keys())
                data["current_month"] = new_months[0] if new_months else None
                log(f"delete_month: новый current_month = {data['current_month']}", level="DEBUG")
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log("delete_month: файл перезаписан", level="DEBUG")
            return True
        else:
            log(f"delete_month: месяц {month} не найден в months", level="DEBUG")
    except Exception as e:
        log(f"delete_month: ошибка: {e}", level="ERROR")
    return False