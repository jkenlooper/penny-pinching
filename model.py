""" The data model for penny-pinching """
import sqlite3
import yaml
import httplib
import doctest

import types
import penny_types

import ConfigParser
import threading
import sys
from decimal import Decimal

config = ConfigParser.ConfigParser()
config.read("app.conf")
db_config = dict(config.items('database'))

thread = threading.local()
def setup_db_connection(handler):
  thread.db = sqlite3.connect(db_config["db_file"])
  thread.db.row_factory = sqlite3.Row # results as dictionary
  thread.db.text_factory = sqlite3.OptimizedUnicode
  try:
    return handler()
  finally:
    thread.db.close() # or something


def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

class SQL(object):
  """ send query to a database and set the data attr with a list of dict
  >>> db_cnx = sqlite3.connect(":memory:")
  >>> sql = SQL(db_cnx=db_cnx)
  >>> sql.query = "create table test(id integer primary key, one, two)"
  >>> sql()
  >>> sql.query = "insert into test (one, two) values (?,?)"
  >>> sql.query_values = ("red fish", "blue fish")
  >>> sql.query_values
  ('red fish', 'blue fish')
  >>> sql()
  >>> sql.query = "select * from test"
  >>> sql.query_values = ()
  >>> sql()
  >>> sql.data == [{'id': 1, 'two': u'blue fish', 'one': u'red fish'}]
  True
  """
  def __init__(self, db_cnx=False):
    if not db_cnx:
      self.db_cnx = thread.db
    else:
      self.db_cnx = db_cnx
    self.cur = self.db_cnx.cursor()
    self._data = {}
    self._query = ''
    self._query_values = ()

  def __call__(self):
    self.cur.execute(self._query, self._query_values)
    self._data = []
    for r in self.cur:
      self._data.append(r)
    print self._data

  @Property
  def query():
    doc="set and display query"
    def fget(self):
      return self._query
    def fset(self, q):
      if isinstance(q, types.StringType):
        self._query = q
    return locals()

  @Property
  def query_values():
    doc="set and display query values"
    def fget(self):
      return self._query_values
    def fset(self, v):
      if isinstance(v, types.TupleType) or isinstance(v, types.ListType):
        self._query_values = v
      else:
        raise TypeError("query values must be in a list")
    return locals()

  @Property
  def data():
    doc="result in a list of dict/s with each key as the column name"
    def fget(self):
      return self._data
    return locals()

class YAML(object):
  ### Tools ###
  def serialize(self):
    """ return a YAML representation of this object """
    def de_decimalize(d):
      for k in d:
        if isinstance(d[k], Decimal):
          d[k] = str(d[k])
      return d
    if isinstance(self.data, types.ListType):
      d = []
      for row in self.data:
        d.append(de_decimalize(row))
    else:
      d = de_decimalize(self.data)
      
    return yaml.safe_dump(d)

  def deserialize(self, yaml_string):
    """ replace all content with the YAML data """
    d = yaml.safe_load(yaml_string)
    for k, v in d.items():
      if k in self._row_data_keys:
        self._data[k] = v

class Model(object):
  pass

class Reference(Model):
  def __init__(self, schema_name, table, column, create):
    super(Reference, self).__init__(schema_name)
    self.table = table
    self.column = column
    self._query_data.update({'table':table, 'column':column})
    self.create = create
  def check(self, v):
    self._query_data['v'] = v
    self._query = "select %(column)s from %(schema_name)s.%(table)s where %(column)s = %%(v)s limit 1" % self._query_data
    try:
      self.cur.execute(self._query, self._query_data)
      self._data = self._dict_result(self.cur.fetchone())
      return bool(self._data)
    except DatabaseError, inst:
      print inst
      print self._query % self._query_data
      return False
    #fail then either insert or return error

  def insert(self, v):
    """ only months can be inserted... """
    if self.create:
      self._query_data['v'] = v
      self._query = "insert into %(schema_name)s.%(table)s (%(column)s, sum, total, end_balance_is_set) values (%%(v)s, '0', '0', 'false')" % self._query_data
      try:
        self.cur.execute(self._query, self._query_data)
      except DatabaseError, inst:
        self.status = httplib.INTERNAL_SERVER_ERROR
        print inst
        print self._query % self._query_data
      return self.status


class RowModel(Model):
  """ Represents a single line of data found or which should be edited/added """
  references=() # (('months', 'year_month'),)
  def __init__(self, schema_name, table):
    super(RowModel, self).__init__(schema_name)
    self._query_data.update({"table":table})
    self.ref_year_month = Reference(schema_name, 'months', 'year_month', True)
    self.ref_chart_cat_meta_name = Reference(schema_name, 'chart_cat_meta', 'name', False)

  def _init_data_by_index(self, value, p_key="id"):
    "initialize the data to the row with the default primary key of id"
    self._query_data.update({'p_key':p_key, p_key:value})
    if value != None:
      self._query = "select * from %(schema_name)s.%(table)s where %(p_key)s = %%(%(p_key)s)s" % self._query_data
      self.cur.execute(self._query, self._query_data)
      self._data = self._dict_result(self.cur.fetchone())
    else:
      self._data = dict(zip(self._row_data_keys, (None,)))
  def _fmt_key_value_data(self):
    my_k = self._row_data_keys
    my_v = [self._data.get(x, None) for x in my_k]
    k_fmt = (" %s," * len(my_k))[:-1]
    k_fmt = k_fmt % (my_k)
    v_fmt = ""
    for key in my_k:
      v_fmt = "%s %%(%s)s," % (v_fmt, key)
    v_fmt = v_fmt[:-1]
    return (k_fmt, v_fmt)
  def _commit(self):
    """ commit the data to the database """
    try:
      print self._query, self._data
      self.cur.execute(self._query, self._data)
    except DatabaseError, inst:
      self.status = httplib.INTERNAL_SERVER_ERROR
      print self._query % self._data
  def check_references(self):
    """ check the references and return False on error """
    for ref in self.references:
      if not ref.check(self._data[ref.column]):
        return False
    return True
        #ref.insert(self._data[ref.column])
  def create_references(self):
    """ create references and return False on error """
    for ref in self.references:
      if ref.create and not ref.insert(self._data[ref.column]):
        return False
    return True

  def insert(self):
    """ insert the data to the databse """
    (k_fmt, v_fmt) = self._fmt_key_value_data()
    qd = self._query_data
    qd.update({'k_fmt':k_fmt, 'v_fmt':v_fmt})
    self._query = "insert into %(schema_name)s.%(table)s (%(k_fmt)s) values (%(v_fmt)s)" % qd
    self._commit()
    if self.status == None: self.status = httplib.CREATED
  def update(self):
    pass
  def delete(self):
    pass

  #TODO: add update, delete methods

  @Property
  def data():
    doc="result data in a dict. can be upadated"
    def fset(self, d):
      self._data.update(d)
    def fget(self):
      return self._data
    return locals()
      
class UserAccounts(Model):
  """ user account data on public table. this includes super users """
  def __init__(self, schema_name):
    super(UserAccounts, self).__init__(schema_name)
    table = 'user_accounts'

class Users(Model):
  """ users for a schema """
  def __init__(self, schema_name):
    super(Users, self).__init__(schema_name)
    table = 'users'
    self._query_data['table'] = table
    self._query = "select * from %(schema_name)s.%(table)s" % self._query_data
    self.cur.execute(self._query, self._query_data)
    self.data = self._dict_result(self.cur.fetchall())

class User(RowModel):
  """ A User account for a schema """
  def __init__(self, schema_name, login=None):
    super(User, self).__init__(schema_name, 'users')
    self._init_data_by_index(login, p_key="login")

class ChartModel(Model):
  """ model for a chart """
  base_query = "select * from %(schema_name)s.chart_cat where type = %%(type)s and year_month isnull"
  month_query = "select * from %(schema_name)s.chart_cat where type = %%(type)s and year_month = %%(year_month)s"
  base_month_query = "%(base_query)s union %(month_query)s order by name, date asc" % {'base_query':base_query, 'month_query':month_query}
  def __init__(self, schema_name, chart_uri):
    super(ChartModel, self).__init__(schema_name)
    self.chart_type = penny_types.type_uri_table[chart_uri]
    self._query_data['type'] = self.chart_type.id
  def _extra_meta_data(self, d):
    m = {'names':[]}
    for row in d:
      m['names'].append(row['name'])
      # total up all Decimals
      for n in [k for (k,v) in row.items() if isinstance(v, Decimal)]:
        before = m.setdefault(n, Decimal("0.00"))
        m[n] = before + row[n]
    self._query = "select * from %(schema_name)s.chart_cat_meta where type = %%(type)s" % self._query_data
    self.cur.execute(self._query, self._query_data)
    meta_data = self._dict_result(self.cur.fetchall())
    grand_sum = Decimal("0.00")
    for row in meta_data:
      if isinstance(row.get('sum'), Decimal):
        grand_sum += row['sum']
    m['grand_sum'] = grand_sum

    return m

class Chart(ChartModel):
  """ meta data and other stuff associated with a base chart """
  def __init__(self, schema_name, chart_uri):
    super(Chart, self).__init__(schema_name, chart_uri)
    self._query = self.base_query % self._query_data
    self.cur.execute(self._query, self._query_data)
    self._data = self._extra_meta_data(self._dict_result(self.cur.fetchall()))

class MonthChart(ChartModel):
  """ meta data and other stuff associated with a monthly chart """
  def __init__(self, schema_name, chart_uri, year_month):
    super(MonthChart, self).__init__(schema_name, chart_uri)
    self._query_data['year_month'] = year_month
    self._query = self.month_query % self._query_data
    self.cur.execute(self._query, self._query_data)
    self._data = self._extra_meta_data(self._dict_result(self.cur.fetchall()))
    
class BaseMonthChart(ChartModel):
  """ meta data and other stuff associated with a base month chart """
  def __init__(self, schema_name, chart_uri, year_month):
    super(BaseMonthChart, self).__init__(schema_name, chart_uri)
    self._query_data['year_month'] = year_month
    self._query = self.base_month_query % self._query_data
    self.cur.execute(self._query, self._query_data)
    self._data = self._extra_meta_data(self._dict_result(self.cur.fetchall()))

class ChartCategories(ChartModel):
  """ All base categories for a chart """
  def __init__(self, schema_name, chart_uri):
    super(ChartCategories, self).__init__(schema_name, chart_uri)
    self._query = self.base_query % self._query_data
    self.cur.execute(self._query, self._query_data)
    self._data = self._dict_result(self.cur.fetchall())

class MonthChartCategories(ChartModel):
  """ All categories for a chart in a month """
  def __init__(self, schema_name, chart_uri, year_month):
    super(MonthChartCategories, self).__init__(schema_name, chart_uri)
    self._query_data['year_month'] = year_month
    self._query = self.month_query % self._query_data
    self.cur.execute(self._query, self._query_data)
    self._data = self._dict_result(self.cur.fetchall())

class BaseMonthChartCategories(ChartModel):
  """ All categories for a chart in a month with base ordered first, unique on name """
  def __init__(self, schema_name, chart_uri, year_month):
    super(BaseMonthChartCategories, self).__init__(schema_name, chart_uri)
    self._query_data['year_month'] = year_month
    self._query = self.base_month_query % self._query_data
    self.cur.execute(self._query, self._query_data)
    d = self._dict_result(self.cur.fetchall())
    unique_rows = {}
    self._data = []
    for row in d:
      if row['name'] not in unique_rows:
        unique_rows[row['name']] = True
        self._data.append(row)


class CategoryMeta(RowModel):
  """ category meta """
  def __init__(self, schema_name, id=None):
    super(CategoryMeta, self).__init__(schema_name, 'chart_cat_meta')
    self._row_data_keys = ('name', 'type', 'sum', 'description')
    self._init_data_by_index(id)

class Category(RowModel):
  """ A single category """
  def __init__(self, schema_name, id=None):
    super(Category, self).__init__(schema_name, 'chart_cat')
    self._row_data_keys = ('name', 'type', 'year_month', 'active', 'sum', 'total', 'starting_balance', 'cap', 'rollover', 'due', 'goal_date', 'goal_total')
    self._init_data_by_index(id)
    self.references = (self.ref_year_month, self.ref_chart_cat_meta_name)

class CategoryItems(Model):
  """ Items associated with a category """
  def __init__(self, schema_name, category_id):
    super(CategoryItems, self).__init__(schema_name)
    # query database and insert data

class CategoryItem(RowModel):
  """ A single category item """
  def __init__(self, schema_name, id=None):
    super(CategoryItem, self).__init__(schema_name, 'chart_cat_items')
    self._row_data_keys = ('title', 'amount', 'description', 'cat_data', 'year_month')
    self._init_data_by_index(id)

if __name__ == "__main__":
  if sys.argv[-1] == '--test':
    doctest.testmod()
