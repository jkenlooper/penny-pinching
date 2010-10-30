#! /usr/bin/env python

import web
import doctest
import yaml
import json
import sqlite3
import os.path
from decimal import Decimal
from datetime import date
import ConfigParser
from auth import read_permission, write_permission, admin_permission
import logging
logging.basicConfig()

logger = logging.getLogger('view')

TRANSACTION_STATUS_ENUM = ['suspect', 'no_receipt', 'receipt', 'scheduled', 'cleared', 'reconciled']

CHART_TYPE_ENUM = ['income', 'expense', 'bill', 'saving']

config = ConfigParser.ConfigParser()
config.read("app.conf")
db_config = dict(config.items('database'))

def get_db_cnx(db_name):
  if db_name:
    db_cnx = sqlite3.connect(os.path.join(db_config["db_directory"], db_name))
    #db_cnx.row_factory = sqlite3.Row # results as dictionary
    db_cnx.text_factory = sqlite3.OptimizedUnicode
    return db_cnx
  else:
    print 'oops'


def initialize_database_tables(db_name):
  if not os.path.exists(os.path.join(db_config["db_directory"], db_name)):
    db_cnx = get_db_cnx(db_name)
    db_cnx.execute("""create table Account(id integer primary key,
        name unique not null,
        active default 1,
        balance default 0,
        balance_date not null);""")
    db_cnx.execute("""create table FinancialTransaction(id integer primary key,
        name not null,
        status integer default 2,
        date not null,
        account not null);""")
    db_cnx.execute("""create table TransactionItem(id integer primary key,
        name not null,
        amount default 0,
        type integer default 0,
        category integer default 0,
        financial_transaction integer not null);""")
    db_cnx.execute("""create table ExpenseCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        minimum default 0,
        maximum default 0,
        allotment not null);""")
    db_cnx.execute("""create table BillCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        minimum default 0,
        maximum default 0,
        allotment not null,
        due);""")
    db_cnx.execute("""create table SavingCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        minimum default 0,
        maximum default 0,
        allotment not null);""")
    db_cnx.execute("""insert into ExpenseCategory (name, allotment) values ("buffer", 0);""")
    db_cnx.execute("""insert into BillCategory (name, allotment) values ("buffer", 0);""")
    db_cnx.execute("""insert into SavingCategory (name, allotment) values ("buffer", 0);""")
    db_cnx.commit()
  

def normalize(l, description):
  d = []
  if l != None and description != None:
    col_names = [x[0] for x in description]
    for row in l:
      d.append(dict(zip(col_names, row)))
  else:
    print l, description
  return d
  
def year_month_day(ymd):
  " validate a str in the format YYYY-MM-DD "
  ymd = str(ymd)
  (year, month, day) = [int(x.strip()) for x in ymd.split('-')]
  return str(date(year, month, day).strftime("%Y-%m-%d"))

def validate(user_input, valid):
  d = dict(zip(valid.keys(), (None,)))
  for k, v in user_input.items():
    if k in valid.keys(): # redundant
      t = valid[k]
      if t == bool:
        if v in ('false', 'False', 'FALSE', 'f', 'F', 0, 'off', 'no', 'OFF', 'No', 'n', 'N'):
          v = False
      if t == Decimal:
        v = str(v)
        v = v.strip()

      if t == 'chart_type': # if string then switch to int
        if v in CHART_TYPE_ENUM:
          v = CHART_TYPE_ENUM.index(v)
        elif (int(v) < len(CHART_TYPE_ENUM)) and (int(v) >= 0):
          v = int(v)
        else:
          raise ValueError("invalid type for chart_type")
      else:
        v = t(v)

      if t == str:
        v = v.strip()
        v = v[:255]
        v = v.lower()
      if t == Decimal:
        v = str(v)
        v = v.strip()
      d[k] = v
    else:
      raise ValueError("keys are not valid. expected: %s but got %s" % (valid.keys(), user_input.keys()))
  return d
    
def dump_data_formatted(data_format, data):
  if data_format == 'yaml':
    return yaml.safe_dump(data)
  elif data_format == 'json':
    return json.write(data)

def load_formatted_data(data_format, data_string):
  if data_format == 'yaml':
    return yaml.safe_load(data_string)
  elif data_format == 'json':
    return json.read(str(data_string))

class ListView(object):
  query = "select * from ExpenseCategory;"
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class Add(object):
  query = "insert into TableName (column1, column2) values (:column1, :column2);"
  valid_data_format = {'name':str, 'balance':Decimal, 'active':bool, 'minimum':Decimal, 'maximum':Decimal, 'allotment':int}
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(data_string=None)
    user_data = load_formatted_data(_user["data_format"], user_input.data_string)
    c = validate(user_data, self.valid_data_format)
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    cur.execute(self.query, c)
    db_cnx.commit()
    return web.created()

class Update(object):
  query = "update Account (name, active, balance, balance_date) values (:name, :active, :balance, :balance_date) where id = :id;"
  valid_data_format = {'id':int, 'name':str, 'active':bool, 'balance':Decimal, 'balance_date':str}
  @write_permission
  def POST(self, db_name, id, _user=None):
    user_input = web.input(data_string=None)
    user_data = {'id':id}
    if _user['data_format'] == 'yaml':
      d = load_formatted_data(_user["data_format"], user_input.data_string)
      user_data.update(d)
    try:
      d = validate(user_data, self.valid_data_format)
    except ValueError:
      return web.badrequest()

    try:
      db_cnx = get_db_cnx(db_name)
      db_cnx.execute(self.query, d)
    except:
      return web.internalerror()
    return web.created()

class UserView(object):
  """ Show the user information for just the user that logged in """
  @read_permission
  def GET(self, db_name, _user=None):
    data = {'db_name':db_name, 'user':[_user,]}
    return dump_data_formatted(_user["data_format"], data)

class DatabaseView(object):
  @read_permission
  def GET(self, db_name, _user=None):
    """ all data from all tables """
    initialize_database_tables(db_name)
    db_cnx = get_db_cnx(db_name)
    data = {}
    tables = ("Account", "FinancialTransaction", "TransactionItem", "ExpenseCategory", "BillCategory", "SavingCategory")
    for t in tables:
      cur = db_cnx.cursor()
      result = cur.execute("select * from %s;" % (t,)).fetchall()
      description = cur.description
      data[t] = normalize(result, description)
    return dump_data_formatted(_user["data_format"], data)

class AccountListView(ListView):
  query = "select * from Account;"

class AccountListActiveView(ListView):
  query = """
    select * from Account left outer join (
      select account as id, total(total) as transaction_total from (
        select * from FinancialTransaction join (
          select total(amount) as total, financial_transaction as id from TransactionItem group by id
        ) using (id)
      ) group by id
    ) using (id) where active = 1;"""

class AccountAdd(Add): 
  query = "insert into Account (name, balance, balance_date) values (:name, :balance, date(current_timestamp));"
  valid_data_format = {'name':str, 'balance':Decimal}

class AccountUpdate(Update): 
  query = "update Account (name, active, balance, balance_date) values (:name, :active, :balance, :balance_date) where id = :id;"
  valid_data_format = {'id':int, 'name':str, 'active':bool, 'balance':Decimal, 'balance_date':year_month_day}

class FinancialTransactionListView(ListView):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id);"

class FinancialTransactionStatusListView(object):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where status = :status;"
  @read_permission
  def GET(self, db_name, status, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, {'status':status}).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class FinancialTransactionClearedSuspectListView(ListView):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where status = 4 or status = 0;"

class FinancialTransactionReceiptNoReceiptScheduledListView(ListView):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where status = 2 or status = 1 or status = 3;"

class FinancialTransactionAdd(Add): 
  query = "insert into FinancialTransaction (name, status, date, account) values (:name, :status, :date, :account);"
  valid_data_format = {'name':str, 'status':int, 'date':year_month_day, 'account':int}

class FinancialTransactionItemAdd(object):
  """ adding a transaction with items """
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(data_string=None)
    user_data = load_formatted_data(_user["data_format"], str(user_input.data_string))
    t = validate(user_data, {'name':str, 'status':int, 'date':year_month_day, 'account':int, 'items':list})
    db_cnx = get_db_cnx(db_name)
    self.cur = db_cnx.cursor()
    self.cur.execute("insert into FinancialTransaction (name, status, date, account) values (:name, :status, :date, :account);", t)
    db_cnx.commit()
    inserted_transaction_id = self.cur.execute("select last_insert_rowid() as id;").next()[0]
    validated_items = []
    v_i = {'name':str, 'amount':Decimal, 'type':'chart_type', 'category':int}
    for item in t['items']:
      item = validate(item, v_i)
      item['financial_transaction'] = inserted_transaction_id
      if item['type'] != 0:
        self._update_category_balance(item)
        item['amount'] = "-%s" % (item['amount'])

      validated_items.append(item)

    db_cnx.executemany("insert into TransactionItem (name, amount, type, category, financial_transaction) values (:name, :amount, :type, :category, :financial_transaction)", validated_items)
    db_cnx.commit()
    return dump_data_formatted(_user["data_format"], t)

  def _update_category_balance(self, item):
    "Update the category balance from the item amount"
    if item['type'] == 1:
      table = "ExpenseCategory"
    elif item['type'] == 2:
      table = "BillCategory"
    elif item['type'] == 3:
      table = "SavingCategory"
    category_select = "select * from %s where id = :id;" % (table)
    category_update = "update %s set balance = :balance where id = :id;" % (table)
     
    category = normalize(self.cur.execute(category_select, {'id':item['category']}), self.cur.description)
    if len(category):
      category = category[0]
      print "%s > %s" % (float(item['amount']), float(category['balance']))
      if float(item['amount']) > float(category['balance']):
        print "item amount exceds category balance"
        item_amount_over = float(item['amount']) - float(category['balance'])
        buffer_category = normalize(self.cur.execute(category_select, {'id':0}), self.cur.description)
        if len(buffer_category):
          buffer_category = buffer_category[0]
          if item_amount_over > float(buffer_category['balance']):
            print "item amount over exceds buffer balance"
          else:
            print "splitting item amount with buffer balance"
            b = {'name':item['name'], 'amount':item_amount_over, 'type':item['type'], 'category':0}
            buffer_item = validate(b, v_i) 
            buffer_balance = Decimal(str(float(buffer_category['balance'])-float(item_amount_over)))
            self.cur.execute(category_update, {'balance':str(buffer_balance), 'id':0})
            validated_items.append(buffer_item)
            item['amount'] = category['balance']
        else:
          print "no buffer found"

      balance = Decimal(str(float(category['balance'])-float(item['amount'])))
      self.cur.execute(category_update, {'balance':str(balance), 'id':item['category']})
    else:
      print "no category"


class FinancialTransactionItemListView(object):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id);"
  subquery = "select * from TransactionItem where financial_transaction = :id;"
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query).fetchall(), cur.description)
    for transaction in data:
      items = normalize(cur.execute(self.subquery, {'id':transaction['id']}), cur.description)
      transaction['items'] = items
    return dump_data_formatted(_user["data_format"], data)

class TransactionItemListView(ListView):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction)";

class ExpenseCategoryListView(ListView):
  query = "select * from ExpenseCategory;"

class ExpenseCategoryListActiveView(ListView):
  query = "select * from ExpenseCategory where active = 1;"

class ExpenseCategoryAdd(Add):
  query = "insert into ExpenseCategory (name, balance, minimum, maximum, allotment) values (:name, :balance, :minimum, :maximum, :allotment)"
  valid_data_format = {'name':str, 'balance':Decimal, 'minimum':Decimal, 'maximum':Decimal, 'allotment':int}

class BillCategoryListView(ListView):
  query = "select * from BillCategory;"

class BillCategoryListActiveView(ListView):
  query = "select * from BillCategory where active = 1;"

class SavingCategoryListView(ListView):
  query = "select * from SavingCategory;"

class SavingCategoryListActiveView(ListView):
  query = "select * from SavingCategory where active = 1;"

class AllCategoryListActiveView(object):
  query = {'expense':"select * from ExpenseCategory where active = 1;",
           'bill':"select * from BillCategory where active = 1;",
           'saving':"select * from SavingCategory where active = 1;"}
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = {}
    for (t, q) in self.query.items():
      data[t] = normalize(cur.execute(q).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class TotalBalanceView(object):
  query_expense = "select total(balance) as total from ExpenseCategory where active = 1;"
  query_bill = "select total(balance) as total from BillCategory where active = 1;"
  query_saving = "select total(balance) as total from SavingCategory where active = 1;"
  query_transaction = """select total(transaction_total) as total from Account left outer join (
        select account as id, total(total) as transaction_total from (
          select account, total from FinancialTransaction join (
            select total(amount) as total, financial_transaction as id from TransactionItem group by id
          ) using (id)
        ) group by id
      ) using (id) where active = 1;"""
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    expense_data = normalize(cur.execute(self.query_expense).fetchall(), cur.description)[0]
    bill_data = normalize(cur.execute(self.query_bill).fetchall(), cur.description)[0]
    saving_data = normalize(cur.execute(self.query_saving).fetchall(), cur.description)[0]
    transaction_data = normalize(cur.execute(self.query_transaction).fetchall(), cur.description)[0]
    category_total = sum((float(expense_data['total']), float(bill_data['total']), float(saving_data['total'])))
    data = {'expense':expense_data['total'],
        'bill':bill_data['total'],
        'saving':saving_data['total'],
        'transaction':transaction_data['total'],
        'category_total':category_total}
    data['available'] = str(Decimal(str(float(transaction_data['total']) - category_total)))
    return dump_data_formatted(_user["data_format"], data)


class PeriodFinancialTransactionListView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  @read_permission
  def GET(self, db_name, period, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class PeriodFinancialTransactionItemListView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :id;"
  @read_permission
  def GET(self, db_name, period, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    for transaction in data:
      items = normalize(cur.execute(self.subquery, {'id':transaction['id']}), cur.description)
      transaction['items'] = items
    return dump_data_formatted(_user["data_format"], data)

class PeriodFinancialTransactionAccountListView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start and account = :account order by date"
  @read_permission
  def GET(self, db_name, period, account, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day, 'account':int})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class PeriodFinancialTransactionItemAccountListView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start and account = :account order by date"
  subquery = "select * from TransactionItem where financial_transaction = ?;"
  @read_permission
  def GET(self, db_name, period, account, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day, 'account':int})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    for transaction in data:
      items = normalize(cur.execute(self.subquery, (transaction['id'])), cur.description)
      transaction['items'] = items
    return dump_data_formatted(_user["data_format"], data)

class PeriodItemsView(object):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction) where date <= :end and date >= :start order by date";
  @read_permission
  def GET(self, db_name, period, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class PeriodItemsCategoryView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 1 and category = :category_id;"
  @read_permission
  def GET(self, db_name, period, category, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day, 'category':int})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    items = []
    for transaction in data:
      valid_sub_data = validate({'transaction_id':transaction['id'], 'category':category}, {'transaction_id':int, 'category_id':int})
      items.append(normalize(cur.execute(self.subquery, valid_sub_data), cur.description))
    return dump_data_formatted(_user["data_format"], items)

class PeriodTransactionItemListView(PeriodItemsView):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction) where date <= :end and date >= :start order by date";

class PeriodTransactionItemExpenseListView(PeriodItemsView):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction) where date <= :end and date >= :start and type = 1 order by date";

class PeriodTransactionItemExpenseCategoryListView(PeriodItemsCategoryView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 1 and category = :category_id;"

class PeriodTransactionItemBillListView(PeriodItemsView):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction) where date <= :end and date >= :start and type = 2 order by date";

class PeriodTransactionItemBillCategoryListView(PeriodItemsCategoryView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 2 and category = :category_id;"

class PeriodTransactionItemSavingListView(PeriodItemsView):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction) where date <= :end and date >= :start and type = 3 order by date";

class PeriodTransactionItemSavingCategoryListView(PeriodItemsCategoryView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 3 and category = :category_id;"

