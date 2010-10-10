#! /usr/bin/env python

import web
import doctest
import sys
from base64 import b64decode
import yaml
import sqlite3
import os.path
import httplib
from decimal import Decimal
from datetime import date

import ConfigParser

TRANSACTION_STATUS_ENUM = ('suspect', 'no_receipt', 'receipt', 'scheduled', 'cleared', 'reconciled')

CHART_TYPE_ENUM = ['income', 'expense', 'bill', 'saving']
period = "([0-9]{4}-[0-9]{1,2}-[0-9]{1,2}\.[0-9]{4}-[0-9]{1,2}-[0-9]{1,2})"
urls = (
    '/', 'IndexPage',
    '/transactions\.html', 'TransactionsPage',
    '/categories\.html', 'CategoriesPage',
    '/([a-z]+)/authorize/?', 'AuthorizeView', # GET

    '/([a-z]+)/?', 'DatabaseView', # GET

    '/([a-z]+)/account-list/?', 'AccountListView', # GET
    '/([a-z]+)/account/?', 'AccountAdd', # POST
    '/([a-z]+)/account/([0-9]+)/?', 'AccountView', # GET
    '/([a-z]+)/account/([0-9]+)/?', 'AccountUpdate', # POST delete attr

    '/([a-z]+)/financial-transaction-list/?', 'FinancialTransactionListView', # GET
    '/([a-z]+)/financial-transaction/?', 'FinancialTransactionAdd', # POST
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionView', # GET
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionUpdate', # POST delete attr

    #financial transactions with items
    '/([a-z]+)/financial-transaction-item-list/?', 'FinancialTransactionItemListView', # GET
    '/([a-z]+)/financial-transaction-item/?', 'FinancialTransactionItemAdd', # POST
    '/([a-z]+)/financial-transaction-item/([0-9]+)/?', 'FinancialTransactionItemView', # GET
    '/([a-z]+)/financial-transaction-item/([0-9]+)/?', 'FinancialTransactionItemUpdate', # POST delete attr

    '/([a-z]+)/transaction-item-list/?', 'TransactionItemListView', # GET
    '/([a-z]+)/transaction-item/?', 'TransactionItemAdd', # POST
    '/([a-z]+)/transaction-item/([0-9]+)/?', 'TransactionItemView', # GET
    '/([a-z]+)/transaction-item/([0-9]+)/?', 'TransactionItemUpdate', # POST delete attr

    '/([a-z]+)/expense-list/?', 'ExpenseCategoryListView', # GET
    '/([a-z]+)/expense/?', 'ExpenseCategoryAdd', # POST
    '/([a-z]+)/expense/([0-9]+)/?', 'ExpenseCategoryView', # GET
    '/([a-z]+)/expense/([0-9]+)/?', 'ExpenseCategoryUpdate', # POST delete attr

    '/([a-z]+)/bill-list/?', 'BillCategoryListView', # GET
    '/([a-z]+)/bill/?', 'BillCategoryAdd', # POST
    '/([a-z]+)/bill/([0-9]+)/?', 'BillCategoryView', # GET
    '/([a-z]+)/bill/([0-9]+)/?', 'BillCategoryUpdate', # POST delete attr

    '/([a-z]+)/saving-list/?', 'SavingCategoryListView', # GET
    '/([a-z]+)/saving/?', 'SavingCategoryAdd', # POST
    '/([a-z]+)/saving/([0-9]+)/?', 'SavingCategoryView', # GET
    '/([a-z]+)/saving/([0-9]+)/?', 'SavingCategoryUpdate', # POST delete attr

    '/([a-z]+)/period/%s/financial-transaction-list/?' % (period), 'PeriodFinancialTransactionListView', # GET
    '/([a-z]+)/period/%s/financial-transaction-item-list/?' % (period), 'PeriodFinancialTransactionItemListView', # GET
    '/([a-z]+)/period/%s/financial-transaction-list/account/([0-9]+)/?' % (period), 'PeriodFinancialTransactionAccountListView', # GET
    '/([a-z]+)/period/%s/financial-transaction-item-list/account/([0-9]+)/?' % (period), 'PeriodFinancialTransactionItemAccountListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/?' % (period), 'PeriodTransactionItemListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/expense/?' % (period), 'PeriodTransactionItemExpenseListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/expense/([0-9]+)/?' % (period), 'PeriodTransactionItemExpenseCategoryListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/bill/?' % (period), 'PeriodTransactionItemBillListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/bill/([0-9]+)/?' % (period), 'PeriodTransactionItemBillCategoryListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/saving/?' % (period), 'PeriodTransactionItemSavingListView', # GET
    '/([a-z]+)/period/%s/transaction-item-list/saving/([0-9]+)/?' % (period), 'PeriodTransactionItemSavingCategoryListView', # GET

    )

app = web.application(urls, globals())
web.config.debug = True

config = ConfigParser.ConfigParser()
config.read("app.conf")
db_config = dict(config.items('database'))

def set_yaml_content():
  web.header('Content-type', "text/yaml; charset=utf-8")

def get_db_cnx(db_name):
  if db_name:
    db_cnx = sqlite3.connect(os.path.join(db_config["db_directory"], db_name))
    #db_cnx.row_factory = sqlite3.Row # results as dictionary
    db_cnx.text_factory = sqlite3.OptimizedUnicode
    return db_cnx
  else:
    print 'oops'

app.add_processor(web.loadhook(set_yaml_content))

def initialize_database_tables(db_name):
  if not os.path.exists(os.path.join(db_config["db_directory"], db_name)):
    db_cnx = get_db_cnx(db_name)
    db_cnx.execute("""create table Account(id integer primary key,
        name unique not null,
        active default true,
        balance default 0,
        balance_date not null);""")
    db_cnx.execute("""create table FinancialTransaction(id integer primary key,
        name not null,
        status integer default 0,
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
        cap default 0,
        allotment not null);""")
    db_cnx.execute("""create table BillCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        cap default 0,
        allotment not null,
        due);""")
    db_cnx.execute("""create table SavingCategory(id integer primary key,
        name unique not null,
        balance default 0,
        active default 1,
        cap default 0,
        allotment not null);""")
  
users = yaml.load(open("users.yaml", 'r'))
def get_http_auth_user_pass():
  return ( b64decode(web.ctx.env['HTTP_AUTHORIZATION'][6:]).split(':', 1)) # 'Basic '
def authorize(permission = ("read", "write", "admin")):
  def decorator(func, *args, **keywords):
    def f(*args, **keywords):
      user, password = None, None
      try:
        user, password = get_http_auth_user_pass()
      except:
        pass
      if user and password:
        user_credentials = check_credentials(user, password, args[1], permission)
        if user_credentials:
          keywords["_user"] = user_credentials
          return func(*args, **keywords)
      web.ctx.status = "401 UNAUTHORIZED"
      web.header("WWW-Authenticate", 'Basic realm="%s %s"'  % (web.websafe(args[1]), permission) )
      web.header('Content-type', "text/html; charset=utf-8")
      return 'unauthorized'
    return f
  return decorator

def check_credentials(login, password, db_name, permission=None):
  """Verifies credentials for login and password.  """

  if login:
    u = users.get(login, None)
    if u != None:
      if db_name == u['database']:
        if password == u['password']:
          if (permission == None) or (u['permission'] in permission):
            return u
          else:
            print "permission denied"
            return False
        else:
          print "Incorrect password"
          return False
      else:
        print "No access for that database"
        return False
    else:
      print "Sorry, login: (%s) is not in the database" % (login)
      return False
  else:
    return False

admin_permission = authorize(permission=("admin",))
write_permission = authorize(permission=("write", "admin"))
read_permission = authorize(permission=("admin", "write", "read"))

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
      if t == Decimal:
        v = str(v)
        v = v.strip()
      d[k] = v
    else:
      raise ValueError("keys are not valid. expected: %s but got %s" % (valid.keys(), user_input.keys()))
  return d
    
def data_formatted(data_format, data):
  if data_format == 'yaml':
    return yaml.safe_dump(data)


from string import Template
class IndexPage(object):
  def GET(self):
    web.header('Content-type', "text/html; charset=utf-8")
    index_template = Template(open('www/index.html', 'r').read())
    content = "This is the index page."
    if os.path.exists('www/data/index_content.html'):
      content = open('www/data/index_content.html', 'r').read()
    database_link_template = "<a href='%(database_name)s/authorize' title='login'>%(database_name)s</a><br/>"
    #db_names = dict(zip([users[x]['database'] for x in users.keys()], (None,))).keys()
    db_names = set()
    for user in users.keys():
      db_names.add(users[user]['database'])
    print db_names
    database_links = ""
    for db_name in db_names:
      database_links = "%s%s" % (database_links, database_link_template % ({'database_name':db_name}))

    return index_template.safe_substitute(content=content, database_links=database_links)

class AuthorizeView(object):
  " login to the requested database "
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    return 'yup'

class ListView(object):
  query = "select * from ExpenseCategory;"
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query).fetchall(), cur.description)
    return data_formatted(_user["data_format"], data)

class Add(object):
  query = "insert into TableName (column1, column2) values (:column1, :column2);"
  valid_data_format = {'name':str, 'balance':Decimal, 'active':bool, 'cap':Decimal, 'allotment':int}
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(data_string=None)
    if _user['data_format'] == 'yaml':
      user_data = yaml.safe_load(user_input.data_string)
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
      user_data.update(yaml.safe_load(user_input.data_string))
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
    return data_formatted(_user["data_format"], data)

class AccountListView(ListView):
  query = "select * from Account;"

class AccountAdd(Add): 
  query = "insert into Account (name, balance, balance_date) values (:name, :balance, date(current_timestamp));"
  valid_data_format = {'name':str, 'balance':Decimal}

class AccountUpdate(Update): 
  query = "update Account (name, active, balance, balance_date) values (:name, :active, :balance, :balance_date) where id = :id;"
  valid_data_format = {'id':int, 'name':str, 'active':bool, 'balance':Decimal, 'balance_date':year_month_day}

class FinancialTransactionAdd(object): 
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(yaml_data_string=None)
    user_data = yaml.safe_load(user_input.yaml_data_string)
    d = validate(user_data, {'name':str, 'status':int, 'date':year_month_day, 'account':int})

    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    cur.execute("insert into FinancialTransaction (name, status, date, account) values (:name, :status, :date, :account);", d)
    db_cnx.commit()
    return web.created()

class FinancialTransactionItemAdd(object):
  """ adding a transaction with items """
  @write_permission
  def POST(self, db_name, _user=None):
    user_input = web.input(data_string=None)
    if _user['data_format'] == 'yaml':
      user_data = yaml.safe_load(user_input.data_string)
    t = validate(user_data, {'name':str, 'status':int, 'date':year_month_day, 'account':int, 'items':list})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    cur.execute("insert into FinancialTransaction (name, status, date, account) values (:name, :status, :date, :account);", t)
    db_cnx.commit()
    inserted_transaction_id = cur.execute("select id from FinancialTransaction where name = :name and status = :status and date = :date and account = :account limit 1;", t).next()[0]
    validated_items = []
    for item in t['items']:
      item = validate(item, {'name':str, 'amount':Decimal, 'type':'chart_type', 'category':int})
      item['financial_transaction'] = inserted_transaction_id
      validated_items.append(item)
    db_cnx.executemany("insert into TransactionItem (name, amount, type, category, financial_transaction) values (:name, :amount, :type, :category, :financial_transaction)", validated_items)
    db_cnx.commit()


class FinancialTransactionItemListView(object):
  @read_permission
  def GET(self, db_name, _user=None):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute("select * from FinancialTransaction;").fetchall(), cur.description)
    for transaction in data:
      items = normalize(cur.execute("select * from TransactionItem where financial_transaction = ?;", (transaction['id'])), cur.description)
      transaction['items'] = items
    return data_formatted(_user["data_format"], data)

class ExpenseCategoryListView(ListView):
  query = "select * from ExpenseCategory;"

class ExpenseCategoryAdd(Add):
  query = "insert into ExpenseCategory (name, balance, active, cap, allotment) values (:name, :balance, :active, :cap, :allotment)"
  valid_data_format = {'name':str, 'balance':Decimal, 'active':bool, 'cap':Decimal, 'allotment':int}

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
    return data_formatted(_user["data_format"], data)

class PeriodFinancialTransactionItemListView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = ?;"
  @read_permission
  def GET(self, db_name, period, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    for transaction in data:
      items = normalize(cur.execute(self.subquery, (transaction['id'])), cur.description)
      transaction['items'] = items
    return data_formatted(_user["data_format"], data)

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
    return data_formatted(_user["data_format"], data)

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
    return data_formatted(_user["data_format"], data)

class PeriodItemsView(object):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = ?;"
  @read_permission
  def GET(self, db_name, period, _user=None):
    k = ('start', 'end')
    d = dict(zip(k,period.split(".")))
    valid_data = validate(d, {'start':year_month_day, 'end':year_month_day})
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    data = normalize(cur.execute(self.query, valid_data).fetchall(), cur.description)
    items = []
    for transaction in data:
      items.append(normalize(cur.execute(self.subquery, (transaction['id'])), cur.description))
    return data_formatted(_user["data_format"], items)

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
    return data_formatted(_user["data_format"], items)

class PeriodTransactionItemListView(PeriodItemsView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = ?;"

class PeriodTransactionItemExpenseListView(PeriodItemsView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = ? and type = 1;"

class PeriodTransactionItemExpenseCategoryListView(PeriodItemsCategoryView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 1 and category = :category_id;"

class PeriodTransactionItemBillListView(PeriodItemsView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = ? and type = 2;"

class PeriodTransactionItemBillCategoryListView(PeriodItemsCategoryView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 2 and category = :category_id;"

class PeriodTransactionItemSavingListView(PeriodItemsView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = ? and type = 3;"

class PeriodTransactionItemSavingCategoryListView(PeriodItemsCategoryView):
  query = "select * from FinancialTransaction where date <= :end and date >= :start order by date"
  subquery = "select * from TransactionItem where financial_transaction = :transaction_id and type = 3 and category = :category_id;"

if __name__ == "__main__":
  if sys.argv[-1] == '--test':
    doctest.testmod()
  elif sys.argv[-1] == '--fcgi':
    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    app.run()
  else:
    app.run()

