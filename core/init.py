# core/init.py
import core.state as state
from core.month_operations import update_month_selector
from core.tree_builder import refresh_ui
from storage import load_data

def init_data():
    incomes, root_expenses, root_investments, current_month, available_months = load_data()
    state.incomes, state.root_expenses, state.root_investments, state.current_month, state.available_months = incomes, root_expenses, root_investments, current_month, available_months
    update_month_selector()
    refresh_ui()