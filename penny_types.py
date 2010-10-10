import re

class Type(object):
  def __init__(self, is_expense, id, title, chart_class):
    self.id = id
    self.title = title
    self.uri = re.sub(" ", "-", title.lower())
    self.is_expense = is_expense
    self.chart_class = chart_class #PlannedChart
    self.category_attr_list = ["id", "name", "type", "year_month", "active", "sum", "total", "starting_balance", "cap", "rollover"]
    if chart_class == "BillsChart":
      self.category_attr_list.append("due")
    elif chart_class == "SavingsChart":
      self.category_attr_list.extend(("goal_date", "goal_total"))

types = (
    #Type(True, 'upe', 'Unplanned Expense', "UnPlannedChart"),
    Type(True, 'pec', 'Planned Expense', "PlannedChart"),
    #Type(False, 'upi', 'Unplanned Income', "UnPlannedChart"),
    Type(False, 'pic', 'Planned Income', "PlannedChart"),
    Type(True, 'bill', 'Bills', "BillsChart"),
    Type(True, 'savings_e', 'Savings', "SavingsChart"),
    Type(None, 'transfer', 'Transfer', "NoChart"),
    #Type(False, 'transfer_i', 'Transfer Income', 'NoChart'),
    #Type(True, 'ble', 'Balance Expense'),
    #Type(False, 'bli', 'Balance Income'),
    )
type_list = [type.id for type in types]
type_id_table = dict(zip([type.id for type in types], types))
type_uri_table = dict(zip([type.uri for type in types], types))
