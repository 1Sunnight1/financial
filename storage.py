# storage.py
import json
import os
from datetime import datetime
from logger import log
from models import CategoryNode

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "finance_data.json")

def get_current_month():
    """Возвращает текущий месяц в формате YYYY-MM"""
    return datetime.now().strftime("%Y-%m")

def save_data(income, root_expenses, root_investments, month=None):
    """Сохраняет данные за указанный месяц (по умолчанию текущий)"""
    log(f"save_data вход: month={month}, income={income}")
    if month is None:
        month = get_current_month()
    log(f"save_data вход: month={month}, income={income}")
    os.makedirs(DATA_DIR, exist_ok=True)
    log(f"save_data: данные записаны в {DATA_FILE}") 

    # Загружаем существующие данные, если файл есть
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

    # Сохраняем деревья в словари
    expenses_dict = {}
    for child in root_expenses.children:
        expenses_dict[child.name] = child.to_dict(for_expense=True)
    investments_dict = {}
    for child in root_investments.children:
        investments_dict[child.name] = child.to_dict(for_expense=False)

    # Обновляем данные за указанный месяц
    data["months"][month] = {
        "income": income,
        "expenses": expenses_dict,
        "investments": investments_dict
    }
    data["current_month"] = month

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_data(month=None):
    """Загружает данные за указанный месяц (по умолчанию текущий). Возвращает (income, root_expenses, root_investments)"""
    root_exp = CategoryNode("__ROOT_EXPENSES__")
    root_inv = CategoryNode("__ROOT_INVESTMENTS__")

    if not os.path.exists(DATA_FILE):
        return 0.0, root_exp, root_inv, get_current_month(), []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return 0.0, root_exp, root_inv, get_current_month(), []
            data = json.loads(content)
    except json.JSONDecodeError:
        return 0.0, root_exp, root_inv, get_current_month(), []

    # Проверка: старый формат (без months) -> конвертируем
    if "months" not in data:
        # Конвертация старого формата
        old_income = data.get("monthly_income", 0.0)
        old_expenses = data.get("expenses", {})
        old_investments = data.get("investments", {})
        current_month = get_current_month()
        data = {"months": {}, "current_month": current_month}
        # Сохраняем как данные за текущий месяц
        data["months"][current_month] = {
            "income": old_income,
            "expenses": old_expenses,
            "investments": old_investments
        }
        # Перезаписываем файл в новом формате
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    if month is None:
        month = data.get("current_month", get_current_month())

    # Получаем список доступных месяцев
    available_months = sorted(data.get("months", {}).keys())

    # Если запрошенный месяц отсутствует, создаём пустые данные для него
    if month not in data["months"]:
        return 0.0, root_exp, root_inv, month, available_months

    month_data = data["months"][month]
    income = month_data.get("income", 0.0)

    # Восстанавливаем деревья
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

    return income, root_exp, root_inv, month, available_months

def get_available_months():
    """Возвращает список доступных месяцев (отсортированный)"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        months = data.get("months", {}).keys()
        return sorted(months)
    except:
        return []

def set_current_month(month):
    """Устанавливает текущий месяц в файле (без загрузки данных)"""
    if not os.path.exists(DATA_FILE):
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["current_month"] = month
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        pass