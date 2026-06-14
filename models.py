# models.py
class CategoryNode:
    """Узел дерева расходов или инвестиций"""
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.forecast = None   # None = нет явного значения, вычислять из детей
        self.actual = None     # None = нет явного значения, вычислять из детей
        self.amount = 0.0      # для инвестиций

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)

    def find_child(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return None

    def get_path(self):
        path = []
        node = self
        while node.parent is not None:
            path.insert(0, node.name)
            node = node.parent
        return path

    # --- Методы для суммирования по дереву расходов ---
    def total_forecast(self):
        if self.forecast is not None:
            return self.forecast
        total = 0.0
        for child in self.children:
            total += child.total_forecast()
        return total

    def total_actual(self):
        if self.actual is not None:
            return self.actual
        total = 0.0
        for child in self.children:
            total += child.total_actual()
        return total

    # --- Для инвестиций ---
    def total_amount(self):
        total = self.amount
        for child in self.children:
            total += child.total_amount()
        return total

    # --- Сериализация ---
    def to_dict(self, for_expense=True):
        result = {}
        if for_expense:
            if self.forecast is not None:
                result["forecast"] = self.forecast
            if self.actual is not None:
                result["actual"] = self.actual
        else:
            if self.amount != 0.0:
                result["amount"] = self.amount
        if self.children:
            result["children"] = {}
            for child in self.children:
                result["children"][child.name] = child.to_dict(for_expense)
        return result

    @classmethod
    def from_dict(cls, name, data, for_expense=True, parent=None):
        node = cls(name, parent=parent)
        if for_expense:
            if "forecast" in data:
                node.forecast = data["forecast"]
            if "actual" in data:
                node.actual = data["actual"]
        else:
            if "amount" in data:
                node.amount = data["amount"]
        children_dict = data.get("children", {})
        for child_name, child_data in children_dict.items():
            child_node = cls.from_dict(child_name, child_data, for_expense, parent=node)
            node.add_child(child_node)
        return node