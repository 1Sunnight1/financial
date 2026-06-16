#core/utils.py
import core.state as state

def get_all_expense_paths():
    """Возвращает список всех путей категорий расходов"""
    paths = []
    def walk(node, current):
        for child in node.children:
            new_path = current + [child.name]
            paths.append('/'.join(new_path))
            walk(child, new_path)
    walk(state.root_expenses, [])
    return sorted(paths)

def get_all_investment_paths():
    """Аналогично для инвестиций"""
    paths = []
    def walk(node, current):
        for child in node.children:
            new_path = current + [child.name]
            paths.append('/'.join(new_path))
            walk(child, new_path)
    walk(state.root_investments, [])
    return sorted(paths)

def get_flat_categories(node, current_path=''):
    categories = []
    for child in node.children:
        path = current_path + '/' + child.name if current_path else child.name
        categories.append({'name': child.name, 'path': path, 'node': child})
        categories.extend(get_flat_categories(child, path))
    return categories

def get_category_by_path(root_node, path):
    parts = path.split('/')
    node = root_node
    for part in parts:
        node = node.find_child(part)
        if node is None:
            return None
    return node

def get_all_leaf_categories(node, parent_path=""):
    """Возвращает список путей всех листовых категорий (без детей)"""
    paths = []
    for child in node.children:
        current_path = f"{parent_path}/{child.name}" if parent_path else child.name
        if not child.children:
            paths.append(current_path)
        else:
            paths.extend(get_all_leaf_categories(child, current_path))
    return paths

def get_all_categories(node, parent_path=""):
    """Возвращает список путей всех категорий (включая родительские)"""
    paths = []
    for child in node.children:
        current_path = f"{parent_path}/{child.name}" if parent_path else child.name
        paths.append(current_path)
        paths.extend(get_all_categories(child, current_path))
    return paths