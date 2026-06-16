# core/report.py
import core.state as state

def update_report():
    total_incomes = sum(state.incomes.values())
    total_forecast = state.root_expenses.total_forecast()
    total_actual = state.root_expenses.total_actual()
    balance = total_incomes - total_actual
    total_investments = state.root_investments.total_amount()
    report_text = f"""
💰 Доходы: {total_incomes:.2f}
📊 Прогноз расходов: {total_forecast:.2f}
📉 Факт расходов: {total_actual:.2f}
📈 Отклонение: {total_forecast - total_actual:+.2f}
💵 Остаток: {balance:.2f}
💼 Инвестиции всего: {total_investments:.2f}
"""
    state.report_label.set_text(report_text)