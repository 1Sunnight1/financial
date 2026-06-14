# storage.py
import json
import os

from models import CategoryNode

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "finance_data.json")

def save_data(income, root_expenses, root_investments):
    os.makedirs(DATA_DIR, exist_ok=True)
    # Сохраняем только детей корней (не сами корни)
    expenses_dict = {}
    for child in root_expenses.children:
        expenses_dict[child.name] = child.to_dict(for_expense=True)
    investments_dict = {}
    for child in root_investments.children:
        investments_dict[child.name] = child.to_dict(for_expense=False)

    data = {
        "monthly_income": income,
        "expenses": expenses_dict,
        "investments": investments_dict
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_data():
    root_exp = CategoryNode("__ROOT_EXPENSES__")
    root_inv = CategoryNode("__ROOT_INVESTMENTS__")

    if not os.path.exists(DATA_FILE):
        return 0.0, root_exp, root_inv

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print("Предупреждение: файл данных пуст. Созданы новые данные.")
                return 0.0, root_exp, root_inv
            data = json.loads(content)
    except json.JSONDecodeError:
        print("Предупреждение: файл данных повреждён (невалидный JSON). Созданы новые данные.")
        return 0.0, root_exp, root_inv
    except OSError as e:
        print(f"Предупреждение: ошибка доступа к файлу: {e}. Созданы новые данные.")
        return 0.0, root_exp, root_inv

    income = data.get("monthly_income", 0.0)
    exp_data = data.get("expenses", {})
    inv_data = data.get("investments", {})

    for child_name, child_data in exp_data.items():
        if isinstance(child_data, dict):
            child_node = CategoryNode.from_dict(child_name, child_data, for_expense=True, parent=root_exp)
            root_exp.add_child(child_node)
    for child_name, child_data in inv_data.items():
        if isinstance(child_data, dict):
            child_node = CategoryNode.from_dict(child_name, child_data, for_expense=False, parent=root_inv)
            root_inv.add_child(child_node)

    return income, root_exp, root_inv