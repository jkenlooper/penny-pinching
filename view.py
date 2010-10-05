#! /usr/bin/env python

import web
import doctest
import sys
from base64 import b64decode
import penny_types
import yaml
import model
import sqlite3
import os.path
import httplib
from decimal import Decimal

import ConfigParser
import threading

web_status_mapping = {
    httplib.CREATED : web.created,
    httplib.ACCEPTED : web.accepted,
    httplib.INTERNAL_SERVER_ERROR : web.internalerror,
    httplib.PRECONDITION_FAILED : web.preconditionfailed,
    httplib.BAD_REQUEST : web.badrequest,
    }
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'] 

TRANSACTION_STATUS_ENUM = ('suspect', 'no_receipt', 'receipt', 'scheduled', 'cleared', 'reconciled')

editable_chart_types = [type for type in penny_types.types if type.chart_class in ('PlannedChart', 'BillsChart', 'SavingsChart')]
chart_uris = "|".join([type.uri for type in editable_chart_types])
or_months = "|".join(MONTHS)

urls = (
    '/([a-z]+)/?', 'DatabaseView', # GET

    '/([a-z]+)/account/?', 'AccountListView', # GET
    '/([a-z]+)/account/?', 'AccountAdd', # POST
    '/([a-z]+)/account/([a-z]+)/?', 'AccountView', # GET
    '/([a-z]+)/account/([a-z]+)/?', 'AccountUpdate', # POST delete attr

    '/([a-z]+)/financial-transaction/?', 'FinancialTransactionListView', # GET
    '/([a-z]+)/financial-transaction/?', 'FinancialTransactionAdd', # POST
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionView', # GET
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionUpdate', # POST delete attr

    '/([a-z]+)/period/?', 'PeriodListView', # GET
    '/([a-z]+)/period/?', 'PeriodAdd', # POST
    '/([a-z]+)/period/([0-9a-z_-]+)/?', 'PeriodView', # GET
    '/([a-z]+)/period/([0-9a-z_-]+)/?', 'PeriodUpdate', # POST delete attr

    # return list of ids
    '/([a-z]+)/period/([0-9a-z_-]+)/financial-transaction/?', 'PeriodFinancialTransactionListView', # GET
    '/([a-z]+)/period/([0-9a-z_-]+)/financial-transaction/account/([a-z]+)/?', 'PeriodFinancialTransactionAccountListView', # GET
    '/([a-z]+)/period/([0-9a-z_-]+)/transaction-item/?', 'PeriodTransactionItemListView', # GET
    '/([a-z]+)/period/([0-9a-z_-]+)/transaction-item/(%s)/?' % (chart_uris), 'PeriodTransactionItemChartListView', # GET


    #'/([a-z]+)/accounts/(.+)/?', 'AccountView',
    #'/([a-z]+)/([0-9]{4})/(%s)/accounts/(.+)/?' % (or_months), 'MonthlyAccountView',

    ##'/([a-z]+)/(%s)/?' % (chart_uris), 'ChartView',
    '/([a-z]+)/([0-9]{4})/(%s)/(%s)/?' % (or_months, chart_uris), 'MonthlyChartView',

    #'/([a-z]+)/(%s)/categories/?' % (chart_uris), 'ChartCategoriesView', 
    '/([a-z]+)/([0-9]{4})/(%s)/(%s)/categories/?' % (or_months, chart_uris), 'MonthlyChartCategoriesView', 

    ## no monthly views for these
    '/([a-z]+)/category/?', 'ChartCategoryAdd', # add a category with meta (POST)
    '/([a-z]+)/category/([0-9]+)/?', 'ChartCategoryView', # used when editing/viewing a cat (GET, POST)

    '/([a-z]+)/category-item/?', 'ChartCategoryItemAdd',
    '/([a-z]+)/category-item/([0-9]+)/?', 'ChartCategoryItemView',
    '/([a-z]+)/category/([0-9]+)/items/?', 'ChartCategoryItemsView',

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
        balance_date default current_timestamp);""")
    db_cnx.execute("create table FinancialTransaction(id integer primary key, name, status, date, account);")
    db_cnx.execute("create table TransactionItem(id integer primary key, name, amount, type, category, financial_transaction);")

    db_cnx.execute("create table PlannedExpenseCategory(id integer primary key, name, period, amount, type, active, starting, cap, rollover);")
    db_cnx.execute("create table PlannedIncomeCategory(id integer primary key, name, period, amount, type, active, starting, cap, rollover);") #TODO
    db_cnx.execute("create table BillCategory(id integer primary key, name, period, amount, type, active, starting, cap, rollover, due);") #TODO
    db_cnx.execute("create table SavingCategory(id integer primary key, name, period, amount, type, active, starting, cap, rollover);") #TODO
    db_cnx.execute("create table Period(id integer primary key, name, start, end);")
  
users = yaml.load(open("users.yaml", 'r'))
def authorize(permission = ("read", "write", "admin")):
  def decorator(func, *args, **keywords):
    def f(*args, **keywords):
      user, password = None, None
      try:
        user, password = (
            b64decode(web.ctx.env['HTTP_AUTHORIZATION'][6:]) # 'Basic '
            .split(':', 1)
        )
      except:
        pass
      #print user, password, args[1], permission
      if user and password and check_credentials(user, password, args[1], permission):
        return func(*args, **keywords)
      else:
        web.ctx.status = "401 UNAUTHORIZED"
        web.header("WWW-Authenticate", 'Basic realm="%s %s"'  % (web.websafe(args[1]), permission) )
        web.header('Content-type', "text/html; charset=utf-8")
        return 'unauthorized'
    return f
  return decorator

def check_credentials(login, password, db_name, permission=None):
  """Verifies credentials for login and password.  """

  if login:
    #u = db_cnx.execute("select * from User where name = ?", (login,)).fetchone()
    u = users.get(login, None)
    if u != None:
      if db_name == u['database']:
        if password == u['password']:
          if (permission == None) or (u['permission'] in permission):
            return True
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

def add_single_from_yaml(m, yaml_string):
  """ adds a single item to the db and returns status """
  if yaml_string == None:
    return web.badrequest()

  m.deserialize(yaml_string)
  if (not m.check_references()) and (not m.create_references()):
    m.status = httplib.PRECONDITION_FAILED
    status = web_status_mapping.get(m.status, None) 
    return status

  m.insert()
  print m.status
  print web_status_mapping.get(m.status, None)
  status = web_status_mapping.get(m.status, None) 
  return status

def normalize(l, description):
  d = []
  if l != None and description != None:
    col_names = [x[0] for x in description]
    for row in l:
      d.append(dict(zip(col_names, row)))
  else:
    print l, description
  return d
  
    
class DatabaseView(object):
  @read_permission
  def GET(self, db_name):
    """ all data from all tables
    accounts:
    periods:
    """
    print db_name
    initialize_database_tables(db_name)
    db_cnx = get_db_cnx(db_name)
    d = {}
    tables = ("Account", "Period", "FinancialTransaction", "TransactionItem", "PlannedExpenseCategory", "PlannedIncomeCategory", "BillCategory", "SavingCategory")
    for t in tables:
      cur = db_cnx.cursor()
      result = cur.execute("select * from %s;" % (t,)).fetchall()
      description = cur.description
      d[t] = normalize(result, description)
    return yaml.safe_dump(d)

class AccountListView(object):
  @read_permission
  def GET(self, db_name):
    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    return yaml.safe_dump(normalize(cur.execute("select * from Account;").fetchall(), cur.description))
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
      v = t(v)
      if t == str:
        v = v[:255]
      if t == Decimal:
        v = str(v)
      d[k] = v
    else:
      raise ValueError("keys are not valid. expected: %s but got %s" % (valid.keys(), user_input.keys()))
  return d

class AccountAdd(object): 
  @write_permission
  def POST(self, db_name):
    user_input = web.input(yaml_data_string=None)
    user_data = yaml.safe_load(user_input.yaml_data_string)
    d = validate(user_data, {'name':str, 'balance':Decimal})

    db_cnx = get_db_cnx(db_name)
    cur = db_cnx.cursor()
    cur.execute("insert into Account (name, balance) values (:name, :balance);", d)
    #db_cnx.execute("insert into Account (name, balance) values (?, ?)", (d['name'], d['balance']))
    db_cnx.commit()
    print 'something'
    print d
    #return web.internalerror()
    return web.created()

class AccountUpdate(object): 
  @write_permission
  def POST(self, db_name, account_name):
    user_input = web.input(yaml_data_string=None)
    user_data = yaml.safe_load(user_input.yaml_data_string)
    try:
      d = validate(user_data, {'name':str, 'active':bool, 'balance':Decimal, 'balance_date':str})
    except ValueError:
      return web.badrequest()

    try:
      db_cnx = get_db_cnx(db_name)
      db_cnx.execute("update Account (name, active, balance, balance_date) values (:name, :active, :balance, :balance_date) where name = :name;", d)
    except:
      return web.internalerror()
    return web.created()

class ChartView(object):
  """ show the chart name with total and a link to the categories """
  @read_permission
  def GET(self, schema_name, chart_uri):
    type = penny_types.type_uri_table[chart_uri]
    pass
    '/([a-z]+)/([0-9]{4})/(%s)/(%s)/?' % (or_months, chart_uris), 'MonthlyChartView',

class ChartCategoriesView(object):
  @read_permission
  def GET(self, schema_name, chart_uri):
    chart_categories = model.ChartCategories(schema_name, chart_uri)
    return chart_categories.serialize()

class MonthlyChartCategoriesView(ChartCategoriesView):
  @read_permission
  def GET(self, schema_name, year, month, chart_uri):
    year_month = "%s_%s" % (year, month)
    chart_categories = model.BaseMonthChartCategories(schema_name, chart_uri, year_month)
    return chart_categories.serialize()

class ChartCategoryView(object):
  @read_permission
  def GET(self, schema_name, category_id):
    """ return a category """
    category = model.Category(schema_name, id=category_id)
    return category.serialize()

class ChartCategoryAdd(object):
  """ add a category """
  #TODO: create year_month if needed?
    #check references and create missing or return error if can't create references.
  @write_permission
  def POST(self, schema_name):
    user_input = web.input(yaml_data_string=None)
    sql = SQL()
    sql.query = "insert into PlannedExpenseCategory (name, active, starting, rollover, cap, amount) values (?,?,?,?,?,?)"
    m = model.CategoryMeta(schema_name)
    status = add_single_from_yaml(m, user_input.yaml_data_string)
    if status != web.created:
      return status()
    # create the cat
    m = model.Category(schema_name)
    m.deserialize(user_input.yaml_data_string)
    m.insert()
    status = web_status_mapping.get(m.status, None) 
    return status()

class ChartCategoryItemsView(object):
  @read_permission
  def GET(self, schema_name, category_id):
    return 'nothing'
    
class ChartCategoryItemView(object):
  @read_permission
  def GET(self, schema_name, item_id):
    " A single category item "
    item = model.CategoryItem(schema_name, id=item_id)
    return item.serialize()

class ChartCategoryItemAdd(object):
  """ add a single category item """
  pass
  #Model = (model.CategoryItem,)

if __name__ == "__main__":
  if sys.argv[-1] == '--test':
    doctest.testmod()
  elif sys.argv[-1] == '--fcgi':
    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    app.run()
  else:
    app.run()

