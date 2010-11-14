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
from auth import read_permission, write_permission, admin_permission, users
import logging
logging.basicConfig()

logger = logging.getLogger('view')

TRANSACTION_STATUS_ENUM = ['suspect', 'no_receipt', 'receipt', 'scheduled', 'cleared', 'reconciled']

CHART_TYPE_ENUM = ['income', 'expense', 'bill', 'saving']

SETTING = ['expense_allotment',]

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
        allotment default 1);""")
    db_cnx.execute("""create table BillCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        maximum default 0,
        allotment_date,
        repeat_due_date default 0,
        due);""") #TODO: add allotment_amount for bigger bills that will need to save up for
    db_cnx.execute("""create table SavingCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        minimum default 0,
        maximum default 0,
        allotment_amount default 0,
        allotment_date,
        repeat_date default 0,
        allotment default 1);""")
    db_cnx.execute("""create table Setting(id integer primary key,
        name unique not null,
        setting default 0);""")
    db_cnx.execute("""insert into ExpenseCategory (name, allotment) values ("buffer", 0);""")
    db_cnx.execute("""insert into Setting (name, setting) values ("expense_allotment", 50);""")
    db_cnx.commit()

for db_name in set([users[name]['database'] for name in users]):
  initialize_database_tables(db_name)

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
      elif t == 'status': # if string then switch to int
        if v in TRANSACTION_STATUS_ENUM:
          v = TRANSACTION_STATUS_ENUM.index(v)
        elif (int(v) < len(TRANSACTION_STATUS_ENUM)) and (int(v) >= 0):
          v = int(v)
        else:
          raise ValueError("invalid type for status")
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

class IDView(object):
  query = "select * from ExpenseCategory where id = :id;"
  @read_permission
  def GET(self, db_name, id, _user=None):
    db_cnx = get_db_cnx(db_name)
    user_data = {'id':id}
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, user_data).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class ListView(object):
  query = "select * from ExpenseCategory;"
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class OrderedListView(ListView):
  """ Attach the 'order by' to end of query """
  query = "select * from ExpenseCategory"
  default_order = 'date'
  valid_order_by = ['name asc', 'name desc']
  @read_permission
  def GET(self, db_name, _user=None):
    user_input = web.input(order_by=None)
    if user_input.order_by in self.valid_order_by:
      self.query = " ".join((self.query, 'order by', user_input.order_by, ';'))
    else:
      self.query = " ".join((self.query, 'order by', self.default_order, ';'))
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class Add(object):
  query = "insert into TableName (column1, column2) values (:column1, :column2);"
  valid_data_format = {'name':str, 'balance':Decimal, 'active':bool, 'minimum':Decimal, 'maximum':Decimal, 'allotment':int}
  def check_data(self, data):
    """ Allow subclasses to check data before inserting """
    return data
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(data_string=None)
    user_data = load_formatted_data(_user["data_format"], user_input.data_string)
    c = validate(user_data, self.valid_data_format)
    db_cnx = get_db_cnx(db_name)
    self.cur = db_cnx.cursor()
    c = self.check_data(c)
    self.cur.execute(self.query, c)
    db_cnx.commit()
    return web.created()

class Update(object):
  query = "update Account set name = :name, active = :active where id = :id;"
  valid_data_format = {'id':int, 'name':str, 'active':bool}
  def check_data(self, data):
    """ Allow subclasses to check data before inserting """
    return data
  @write_permission
  def POST(self, db_name, id, _user=None):
    user_input = web.input(data_string=None)
    user_data = {'id':id}
    d = load_formatted_data(_user["data_format"], user_input.data_string)
    user_data.update(d)
    d = validate(user_data, self.valid_data_format)

    #try:
    db_cnx = get_db_cnx(db_name)
    self.cur = db_cnx.cursor()
    d = self.check_data(d)
    self.cur.execute(self.query, d)
    db_cnx.commit()
    #except:
      #return web.internalerror()
    return web.created()

class UserView(object):
  """ Show the user information for just the user that logged in """
  @read_permission
  def GET(self, db_name, _user=None):
    data = {'db_name':db_name, 'user':[_user,]}
    return dump_data_formatted(_user["data_format"], data)

class DatabaseInitialize(object):
  @admin_permission
  def GET(self, db_name, _user=None):
    """ create the database """
    web.header('Content-type', "text/html; charset=utf-8")
    initialize_database_tables(db_name)
    return web.created();

class DatabaseView(object):
  @read_permission
  def GET(self, db_name, _user=None):
    """ all data from all tables """
    #initialize_database_tables(db_name)
    db_cnx = get_db_cnx(db_name)
    data = {}
    tables = ("Account", "FinancialTransaction", "TransactionItem", "ExpenseCategory", "BillCategory", "SavingCategory")
    for t in tables:
      cur = db_cnx.cursor()
      result = cur.execute("select * from %s;" % (t,)).fetchall()
      description = cur.description
      data[t] = normalize(result, description)
    return dump_data_formatted(_user["data_format"], data)

class AccountListView(object):
  query = """
    select * from Account left outer join (
      select account as id, total(total) as transaction_total from (
        select * from FinancialTransaction join (
          select total(amount) as total, financial_transaction as id from TransactionItem group by id
        ) using (id)
      ) group by id
    ) using (id) order by id;"""
  status_query = """
    select id, status_total from Account left outer join (
      select account as id, total(total) as status_total from (
        select * from FinancialTransaction join (
          select total(amount) as total, financial_transaction as id from TransactionItem group by id
        ) using (id) where status = :status 
      ) group by id
    ) using (id) order by id;"""

  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query).fetchall(), cur.description)
    for status in range(0, len(TRANSACTION_STATUS_ENUM)):
      status_name = TRANSACTION_STATUS_ENUM[status]
      status_total = normalize(cur.execute(self.status_query, {'status':status}).fetchall(), cur.description)
      for item in data:
        t = status_total[int(item['id'])-1]['status_total']
        if t == None:
          t = 0.00
        item['%s_total' % status_name] = str(Decimal(str(t)))

    for item in data:
      t = item['transaction_total']
      if t == None:
        t = 0.00
      balance = Decimal(item['balance'])
      transaction_total = Decimal(str(t))
      reconciled = Decimal(item['reconciled_total'])
      cleared = Decimal(item['cleared_total'])
      suspect = Decimal(item['suspect_total'])
      receipt = Decimal(item['receipt_total'])
      no_receipt = Decimal(item['no_receipt_total'])
      scheduled = Decimal(item['scheduled_total'])

      #difference = (balance - (reconciled + (cleared + suspect))) - (receipt + no_receipt + scheduled)
      difference = (transaction_total - (receipt + no_receipt + scheduled)) - balance
      item['balance_difference'] = str(difference)

    return dump_data_formatted(_user["data_format"], data)

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
  query = "update Account set name = :name, active = :active, balance = :balance, balance_date = :balance_date where id = :id;"
  valid_data_format = {'id':int, 'name':str, 'active':bool, 'balance':Decimal, 'balance_date':year_month_day}

class ClearedToReconciledUpdate(object):
  """ Set the status of cleared transactions to reconciled in an account if the balance and transaction total of reconciled, cleared, and suspect are equal. """
  @write_permission
  def POST(self, db_name, account_id, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    query = """
      select * from Account left outer join (
        select account as id, total(total) as transaction_total from (
          select * from FinancialTransaction join (
            select total(amount) as total, financial_transaction as id from TransactionItem group by id
          ) using (id) where status = 4 or status = 5 or status = 0
        ) group by id
      ) using (id) where id = :id;"""
    data = normalize(cur.execute(query, {'id':account_id}).fetchall(), cur.description)
    data = data[0]
    if Decimal(str(data['balance'])) == Decimal(str(data['transaction_total'])):
      cur.execute("update FinancialTransaction set status = 5 where account = :id and status = 4;", {'id':int(account_id)})
      db_cnx.commit()
    else:
      print "balance %s != transaction total %s" % (data['balance'], data['transaction_total'])
    return web.accepted()

class FinancialTransactionListView(ListView):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) order by date;"

class FinancialTransactionStatusListView(object):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where status = :status order by date;"
  @read_permission
  def GET(self, db_name, status, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, {'status':status}).fetchall(), cur.description)
    return dump_data_formatted(_user["data_format"], data)

class FinancialTransactionClearedSuspectListView(OrderedListView):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where status = 4 or status = 0"
  valid_order_by = ['name asc', 'name desc', 'total asc', 'total desc', 'date asc', 'date desc']
  default_order = 'date desc'

class FinancialTransactionReceiptNoReceiptScheduledListView(OrderedListView):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where status = 2 or status = 1 or status = 3"
  valid_order_by = ['name asc', 'name desc', 'total asc', 'total desc', 'date asc', 'date desc']
  default_order = 'date desc'

class FinancialTransactionAdd(Add): 
  query = "insert into FinancialTransaction (name, status, date, account) values (:name, :status, :date, :account);"
  valid_data_format = {'name':str, 'status':int, 'date':year_month_day, 'account':int}

class FinancialTransactionStatusUpdate(Update):
  query = "update FinancialTransaction set status = :status where id = :id;"
  valid_data_format = {'status':'status', 'id':int}

class FinancialTransactionItemAdd(object):
  """ adding a transaction with items """
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(data_string=None)
    user_data = load_formatted_data(_user["data_format"], str(user_input.data_string))
    t = validate(user_data, {'name':str, 'status':int, 'date':year_month_day, 'account':int, 'items':list})
    self.db_cnx = get_db_cnx(db_name)
    self.cur = self.db_cnx.cursor()
    self.cur.execute("insert into FinancialTransaction (name, status, date, account) values (:name, :status, :date, :account);", t)
    self.db_cnx.commit()
    self.inserted_transaction_id = self.cur.execute("select last_insert_rowid() as id;").next()[0]
    self.validated_items = []
    self.v_i = {'name':str, 'amount':Decimal, 'type':'chart_type', 'category':int, 'financial_transaction':int}
    for item in t['items']:
      item = validate(item, self.v_i)
      item['financial_transaction'] = self.inserted_transaction_id
      if int(item['type']) != 0:
        self._update_category_balance(item)
        item['amount'] = "-%s" % (item['amount'])
      else:
        available = float(item['amount'])
        available = self._distribute_to_bill_categories(available)
        #TODO: split available between saving and expense
        if available > 0:
          setting_query = "select * from Setting where name = 'expense_allotment';"
          expense_allotment = float(normalize(self.cur.execute(setting_query), self.cur.description)[0]['setting'])

          expense_available = available * (expense_allotment/100.0)
          saving_available = available * ((100.0 - expense_allotment)/100.0)
          available = self._distribute_to_expense_categories(expense_available)
          available = self._distribute_to_saving_categories(available+saving_available)

          self._distribute_to_buffer(available)

      self.validated_items.append(item)

    self.db_cnx.executemany("insert into TransactionItem (name, amount, type, category, financial_transaction) values (:name, :amount, :type, :category, :financial_transaction)", self.validated_items)
    self.db_cnx.commit()
    total_balance_data = get_total_balance_data(self.cur)
    self.cur.execute("update ExpenseCategory set maximum = :max where id = 1;", {'max':total_balance_data['transaction']})
    self.db_cnx.commit()
    return dump_data_formatted(_user["data_format"], t)

  def _distribute_to_bill_categories(self, available):
    "Distribute between bill categories based on allotment date"
    bill_categories = normalize(self.cur.execute("select * from BillCategory join (select date('now') as now) where active = 1 and allotment_date < now and balance != maximum order by due;"), self.cur.description)
    for cat in bill_categories:
      diff = float(cat['maximum']) - float(cat['balance'])
      cat['balance'] = str(Decimal(str(float(cat['balance'])+min(diff, available))))
      if diff < available:
        available = available - diff
      else:
        available = 0
      self.cur.execute("update BillCategory set balance = :balance where id = :id;", cat)
    return available

  def _distribute_to_saving_categories(self, available):
    "Distribute between saving categories that the current date is after the allotment date"
    saving_categories = normalize(self.cur.execute("select * from SavingCategory join(select date('now') as now) where active = 1 and allotment_date < now and cast(balance as numeric) < cast(maximum as numeric);"), self.cur.description) #and allotment_amount < minimum
    saving_allotment_total = int(normalize(self.cur.execute("select total(allotment) as total_allotment from SavingCategory join(select date('now') as now) where active = 1 and allotment_date < now and cast(balance as numeric) < cast(maximum as numeric);"), self.cur.description)[0]['total_allotment'])
    if saving_allotment_total > 0:
      available_remainder = available
      for cat in saving_categories:
        share = (float(cat['allotment'])/float(saving_allotment_total)) * available
        diff = float(cat['minimum']) - float(cat['allotment_amount'])
        change = min(share, diff)
        available_remainder = available_remainder - change
        cat['balance'] = str(Decimal(str(float(cat['balance'])+change)))
        cat['allotment_amount'] = str(Decimal(str(float(cat['allotment_amount'])+change)))
        if (float(cat['allotment_amount']) == float(cat['minimum'])):
          cat['allotment_amount'] = "0.00"
          # set the repeat date
          if cat['repeat_date'] != 0:
            dates = normalize(self.cur.execute("select date(:allotment_date, :repeat_date) as allotment_date", cat), self.cur.description)[0]
            if len(dates):
              cat['allotment_date'] = dates['allotment_date']
        self.cur.execute("update SavingCategory set balance = :balance, allotment_amount = :allotment_amount, allotment_date = :allotment_date where id = :id;", cat)
        self.db_cnx.commit()
      available = available_remainder
    return available

  def _distribute_to_expense_categories(self, available):
    "Distribute the income item between categories based on allotments"
    expense_categories = normalize(self.cur.execute("select * from ExpenseCategory where active=1 order by allotment desc;"), self.cur.description)
    expense_allotment_total = int(normalize(self.cur.execute("select total(allotment) as total_allotment from ExpenseCategory where active=1;"), self.cur.description)[0]['total_allotment'])
    for cat in expense_categories: #update minimums first
      if float(cat['balance']) < float(cat['minimum']):
        diff = float(cat['minimum']) - float(cat['balance'])
        cat['balance'] = str(Decimal(str(float(cat['balance'])+min(diff, available))))
        if diff < available:
          available = available - diff
        else:
          available = 0
        self.cur.execute("update ExpenseCategory set balance = :balance where id = :id;", cat)

    if expense_allotment_total > 0:
      available_remainder = available
      for cat in expense_categories:
        share = (float(cat['allotment'])/float(expense_allotment_total)) * available
        diff = float(cat['maximum']) - float(cat['balance'])
        change = min(share, diff)
        available_remainder = available_remainder - change
        cat['balance'] = str(Decimal(str(float(cat['balance'])+change)))
        self.cur.execute("update ExpenseCategory set balance = :balance where id = :id;", cat)
        self.db_cnx.commit()
      available = available_remainder

    if available > 0:
      extra_allotment_total = 0
      for cat in expense_categories:
        if float(cat['balance']) < float(cat['maximum']):
          extra_allotment_total += int(cat['allotment'])
      if extra_allotment_total > 0:
        available_remainder = available
        for cat in expense_categories:
          if float(cat['balance']) < float(cat['maximum']):
            share = (float(cat['allotment'])/float(extra_allotment_total)) * available
            diff = float(cat['maximum']) - float(cat['balance'])
            change = min(share, diff)
            available_remainder = available_remainder - change
            cat['balance'] = str(Decimal(str(float(cat['balance'])+change)))
            self.cur.execute("update ExpenseCategory set balance = :balance where id = :id;", cat)
        available = available_remainder

    return available

  def _distribute_to_buffer(self, available):
    if available > 0:
      buff = float(normalize(self.cur.execute("select balance from ExpenseCategory where id = 1;"), self.cur.description)[0]['balance'])
      self.cur.execute("update ExpenseCategory set balance = :available where id = 1;", {'available':str(Decimal(str(buff+available)))})


  def _update_category_balance(self, item):
    "Update the category balance from the item amount"
    if int(item['type']) == 1:
      table = "ExpenseCategory"
    elif int(item['type']) == 2:
      table = "BillCategory"
    elif int(item['type']) == 3:
      table = "SavingCategory"
    category_select = "select * from %s where id = :id;" % (table)
    category_update = "update %s set balance = :balance where id = :id;" % (table)

    #print item
     
    category = normalize(self.cur.execute(category_select, {'id':item['category']}), self.cur.description)
    if len(category):
      category = category[0]
      #print "%s > %s" % (float(item['amount']), float(category['balance']))
      if float(item['amount']) > float(category['balance']):
        print "item amount exceds category balance"
        item_amount_over = float(item['amount']) - float(category['balance'])
        buffer_category = normalize(self.cur.execute("select * from ExpenseCategory where id = 1"), self.cur.description)
        if len(buffer_category):
          buffer_category = buffer_category[0]
          if item_amount_over > float(buffer_category['balance']):
            print "item amount over exceds buffer balance"
          else:
            item_amount_over = float("-%s" % (item_amount_over))
            print "splitting item amount with buffer balance %s" % item_amount_over
            b = {'name':item['name'], 'amount':item_amount_over, 'type':item['type'], 'category':0, 'financial_transaction':self.inserted_transaction_id}
            buffer_item = validate(b, self.v_i) 
            buffer_balance = Decimal(str(float(buffer_category['balance'])+float(item_amount_over)))
            self.cur.execute("update ExpenseCategory set balance = :balance where id = 1", {'balance':str(buffer_balance)})
            self.validated_items.append(buffer_item)
            item['amount'] = category['balance']
        else:
          print "no buffer found"

      balance = Decimal(str(float(category['balance'])-float(item['amount'])))
      if int(item['type']) != 2:
        self.cur.execute(category_update, {'balance':str(balance), 'id':item['category']})
        self.db_cnx.commit()

      else: #mark the bill as paid by inactivating it or setting new due date
        if str(category['repeat_due_date']) != '0':
          dates = normalize(self.cur.execute("select date(:allotment_date, :repeat_due_date) as allotment_date, date(:due, :repeat_due_date) as due", category), self.cur.description)[0]
          if len(dates):
            self.cur.execute("update BillCategory set allotment_date = :allotment_date, due = :due, balance = :balance where id = :id", {'allotment_date':dates['allotment_date'], 'due':dates['due'], 'balance':str(balance), 'id':category['id']})
            self.db_cnx.commit()
          else:
            print 'invalid date?'
        else:
          #print "inactivating paid bill"
          self.cur.execute("update BillCategory set active = 0, balance = :balance where id = :id", {'id':item['category'], 'balance':str(balance)})
          self.db_cnx.commit()
    else:
      print "no category"


class FinancialTransactionItemListView(object):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id);"
  #TODO: set account_name in query
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

class FinancialTransactionItemDelete(object):
  query = "delete from FinancialTransaction where id = :id;"
  subquery = "delete from TransactionItem where financial_transaction = :id;"
  @read_permission
  def POST(self, db_name, id, _user=None):
    db_cnx = get_db_cnx(db_name)
    user_data = {'id':id}
    cur = db_cnx.cursor()
    cur.execute(self.query, user_data)
    cur.execute(self.subquery, user_data)
    db_cnx.commit()
    return web.accepted()


class FinancialTransactionItemView(object):
  query = "select * from FinancialTransaction join (select total(amount) as total, financial_transaction as id from TransactionItem group by id) using (id) where id = :id;"
  subquery = "select * from TransactionItem where financial_transaction = :id;"
  @read_permission
  def GET(self, db_name, id, _user=None):
    db_cnx = get_db_cnx(db_name)
    user_data = {'id':id}
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, user_data).fetchall(), cur.description)
    for transaction in data:
      items = normalize(cur.execute(self.subquery, {'id':transaction['id']}), cur.description)
      transaction['items'] = items
    print data
    return dump_data_formatted(_user["data_format"], data)

class TransactionItemListView(ListView):
  query = "select * from TransactionItem join (select date, name as transaction_name, id as financial_transaction from FinancialTransaction group by financial_transaction) using (financial_transaction)";

class SettingView(object):
  query = "select * from Setting where name = :name;"
  @read_permission
  def GET(self, db_name, name, _user=None):
    if name in SETTING:
      db_cnx = get_db_cnx(db_name)
      user_data = {'name':name}
      cur = db_cnx.cursor()
      data = normalize(cur.execute(self.query, user_data).fetchall(), cur.description)
      return dump_data_formatted(_user["data_format"], data)

class SettingUpdate(object):
  query = "update Setting set setting = :setting where name = :name;"
  valid_data_format = {'setting':str}
  @write_permission
  def POST(self, db_name, name, _user=None):
    if name in SETTING:
      user_input = web.input(data_string=None)
      user_data = {'name':name}
      d = load_formatted_data(_user["data_format"], user_input.data_string)
      d = validate(d, self.valid_data_format)
      user_data.update(d)
      db_cnx = get_db_cnx(db_name)
      cur = db_cnx.cursor()
      cur.execute(self.query, user_data)
      db_cnx.commit()
      return web.accepted()

class CategoryAdd(Add):
 def check_data(self, data):
   t = get_total_balance_data(self.cur)
   available = float(t['available'])
   if available < float(data['balance']):
     print "insufficient funds..."
     #TODO: alert user
   return data

class CategoryUpdate(Update):
 def check_data(self, data):
   if 'balance' in data:
     t = get_total_balance_data(self.cur)
     available = float(t['available'])
     balance = float(str(data['balance']))
     if available < balance:
       print "insufficient funds..."
       #TODO: alert user
   return data


class ExpenseCategoryView(IDView):
  query = "select * from ExpenseCategory where id = :id;"

class ExpenseCategoryListView(ListView):
  query = "select * from ExpenseCategory;"

class ExpenseCategoryListActiveView(ListView):
  query = "select * from ExpenseCategory where active = 1;"

class ExpenseCategoryListInActiveView(ListView):
  query = "select * from ExpenseCategory where active = 0;"

class ExpenseCategoryAdd(CategoryAdd):
  query = "insert into ExpenseCategory (name, balance, minimum, maximum, allotment) values (:name, :balance, :minimum, :maximum, :allotment)"
  valid_data_format = {'name':str, 'balance':Decimal, 'minimum':Decimal, 'maximum':Decimal, 'allotment':int}

class ExpenseCategoryUpdate(CategoryUpdate):
  query = "update ExpenseCategory set name = :name, balance = :balance, minimum = :minimum, maximum = :maximum, allotment = :allotment, active = :active where id = :id"
  valid_data_format = {'name':str, 'balance':Decimal, 'minimum':Decimal, 'maximum':Decimal, 'allotment':int, 'id':int, 'active':int}

class ExpenseCategoryUpdateBalance(CategoryUpdate):
  query = "update ExpenseCategory set balance = :balance where id = :id"
  valid_data_format = {'balance':Decimal, 'id':int}

class ExpenseCategoryUpdateActive(CategoryUpdate):
  query = "update ExpenseCategory set active = :active where id = :id"
  valid_data_format = {'active':int, 'id':int}

class BillCategoryView(IDView):
  query = "select * from BillCategory where id = :id;"

class BillCategoryListView(ListView):
  query = "select * from BillCategory;"

class BillCategoryListActiveView(ListView):
  query = "select * from BillCategory where active = 1 order by due;"

class BillCategoryListInActiveView(ListView):
  query = "select * from BillCategory where active = 0 order by due;"

class BillCategoryAdd(CategoryAdd):
  query = "insert into BillCategory (name, balance, maximum, allotment_date, repeat_due_date, due) values (:name, :balance, :maximum, :allotment_date, :repeat_due_date, :due);"
  valid_data_format = {'name':str, 'balance':Decimal, 'maximum':Decimal, 'allotment_date':year_month_day, 'repeat_due_date':str, 'due':year_month_day}

class BillCategoryUpdate(CategoryUpdate):
  query = "update BillCategory set name = :name, balance = :balance, maximum = :maximum, allotment_date = :allotment_date, repeat_due_date = :repeat_due_date, due = :due, active = :active where id = :id"
  valid_data_format = {'name':str, 'balance':Decimal, 'maximum':Decimal, 'allotment_date':year_month_day, 'repeat_due_date':str, 'due':year_month_day, 'active':int, 'id':int}
    
class BillCategoryUpdateActive(CategoryUpdate):
  query = "update BillCategory set active = :active where id = :id"
  valid_data_format = {'active':int, 'id':int}

class SavingCategoryView(IDView):
  query = "select * from SavingCategory where id = :id;"

class SavingCategoryListView(ListView):
  query = "select * from SavingCategory;"

class SavingCategoryListActiveView(ListView):
  query = "select * from SavingCategory where active = 1;"

class SavingCategoryListInActiveView(ListView):
  query = "select * from SavingCategory where active = 0;"

class SavingCategoryAdd(CategoryAdd):
  query = "insert into SavingCategory (name, balance, minimum, maximum, allotment_amount, allotment_date, repeat_date, allotment) values (:name, :balance, :minimum, :maximum, :allotment_amount, :allotment_date, :repeat_date, :allotment);"
  valid_data_format = {'name':str, 'balance':Decimal, 'minimum':Decimal, 'maximum':Decimal, 'allotment_amount':Decimal, 'allotment_date':year_month_day, 'repeat_date':str, 'allotment':int}

class SavingCategoryUpdate(CategoryUpdate):
  query = "update SavingCategory set name = :name, balance = :balance, minimum = :minimum, maximum = :maximum, allotment_amount = :allotment_amount, allotment_date = :allotment_date, repeat_date = :repeat_date, allotment = :allotment, active = :active where id = :id"
  valid_data_format = {'name':str, 'balance':Decimal, 'minimum':Decimal, 'maximum':Decimal, 'allotment_amount':Decimal, 'allotment_date':year_month_day, 'repeat_date':str, 'allotment':int, 'active':int, 'id':int}

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

def get_total_balance_data(cur):
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
  expense_data = normalize(cur.execute(query_expense).fetchall(), cur.description)[0]
  bill_data = normalize(cur.execute(query_bill).fetchall(), cur.description)[0]
  saving_data = normalize(cur.execute(query_saving).fetchall(), cur.description)[0]
  transaction_data = normalize(cur.execute(query_transaction).fetchall(), cur.description)[0]
  category_total = Decimal(str(sum((float(expense_data['total']), float(bill_data['total']), float(saving_data['total'])))))
  data = {'expense':str(Decimal(str(expense_data['total']))),
      'bill':str(Decimal(str(bill_data['total']))),
      'saving':str(Decimal(str(saving_data['total']))),
      'transaction':str(Decimal(str(transaction_data['total']))),
      'category_total':str(category_total)}
  data['available'] = str(float(data['transaction']) - float(category_total))
  return data

class TotalBalanceView(object):
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = get_total_balance_data(cur)

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

