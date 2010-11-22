#! /usr/bin/env python

##  This file is a part of penny-pinching.
##  Copyright (C) 2010 Jake Hickenlooper
##
##  penny-pinching is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affreo General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affreo General Public License for more details.
##
##  You should have received a copy of the GNU Affreo General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.


## This is a quick script to convert the older postgresql penny-pinching data
## (penny schema) and merge it with a newer (jc schema) database to a yaml
## format that can be imported using the client.py script. Whew.

import bpgsql
import types
import yaml
from decimal import Decimal
import ConfigParser

config = ConfigParser.ConfigParser()
config.read("app.conf")
pg_db = dict(config.items('pg_db'))

app_cnx = bpgsql.connect("host=%(host)s dbname=%(dbname)s user=%(user)s password=%(password)s" % pg_db)

class PG(object):
  def __init__(self):
    self.cur = app_cnx.cursor()

  def query(self, q):
    data = {}
    self.cur.execute(q, data)
    return self._dict_result(self.cur.fetchall())

  def _dict_result(self, result_tuple):
    def _create_dict_from_tuple(t):
      field_names = (x[0] for x in self.cur.description)
      d = dict(zip(field_names, t))
      return d

    if result_tuple:
      if isinstance(result_tuple[0], types.ListType):
        l = []
        for t in result_tuple:
          l.append(_create_dict_from_tuple(t))
        return l
      else:
        return _create_dict_from_tuple(result_tuple)

    else:
      return False

data = {}

pg = PG()

data['account'] = []
account_name_map = {}
d = pg.query("select * from penny.accounts_meta_data;")
i = 1
for item in d:
  data['account'].append({'balance':str(item['real_balance']), 'name':item['name']})
  account_name_map[item['name']] = i
  i += 1
account_max = i

account_id_map = {}
d = pg.query("select * from penny.accounts_data;")
for item in d:
  account_id_map[item['id']] = account_name_map[item['name']] # 31:1

expense_name_map = {}
data['expense'] = []
d = pg.query("select name from penny.chart_cat_data where type = 'pec' or type = 'upe' group by name;")
i = 1
for item in d:
  data['expense'].append({'name':item['name'], 'balance':0, 'minimum':0, 'maximum':0, 'allotment':1})
  expense_name_map[item['name']] = i
  i += 1
expense_max = i

expense_id_map = {}
d = pg.query("select * from penny.chart_cat_data where type = 'pec' or type = 'upe';")
for item in d:
  expense_id_map[item['id']] = expense_name_map[item['name']]
  t = pg.query("select sum(amount) as total from penny.items_data where category = %i and type in ('pec', 'upe');" % item['id'])
  if t and t[0]['total'] != None:
    total = Decimal(str(t[0]['total']))
    b = Decimal(str(data['expense'][expense_name_map[item['name']]-1]['balance']))
    data['expense'][expense_name_map[item['name']]-1]['balance'] = str(b + total)
    data['expense'][expense_name_map[item['name']]-1]['maximum'] = str(b + total)

bill_name_map = {}
data['bill'] = []
d = pg.query("select name from penny.chart_cat_data where type = 'bill' group by name;")
i = 1
for item in d:
  data['bill'].append({'name':item['name'], 'balance':0, 'maximum':0, 'allotment_date':'2010-11-13', 'repeat_due_date':0, 'due':'2010-11-13'})
  bill_name_map[item['name']] = i
  i += 1
bill_max = i

bill_id_map = {}
d = pg.query("select * from penny.chart_cat_data where type = 'bill';")
for item in d:
  bill_id_map[item['id']] = bill_name_map[item['name']]
  t = pg.query("select sum(amount) as total from penny.items_data where category = %i and type = 'bill';" % item['id'])
  if t and t[0]['total'] != None:
    total = Decimal(str(t[0]['total']))
    b = Decimal(str(data['bill'][bill_name_map[item['name']]-1]['balance']))
    data['bill'][bill_name_map[item['name']]-1]['balance'] = str(b + total)
    data['bill'][bill_name_map[item['name']]-1]['maximum'] = str(b + total)

saving_name_map = {}
data['saving'] = []
d = pg.query("select name from penny.chart_cat_data where type = 'savings_e' group by name;")
i = 1
for item in d:
  data['saving'].append({'name':item['name'], 'balance':0, 'minimum':0, 'maximum':0, 'allotment_amount':0, 'allotment_date':'2010-11-13', 'repeat_date':0, 'allotment':1})
  saving_name_map[item['name']] = i
  i += 1
saving_max = i

saving_id_map = {}
d = pg.query("select * from penny.chart_cat_data where type = 'savings_e';")
for item in d:
  saving_id_map[item['id']] = saving_name_map[item['name']]
  t = pg.query("select sum(amount) as total from penny.items_data where category = %i and type = 'savings_e';" % item['id'])
  if t and t[0]['total'] != None:
    total = Decimal(str(t[0]['total']))
    b = Decimal(str(data['saving'][saving_name_map[item['name']]-1]['balance']))
    data['saving'][saving_name_map[item['name']]-1]['balance'] = str(b + total)
    data['saving'][saving_name_map[item['name']]-1]['maximum'] = str(b + total)

income_name_map = {}
data['income'] = []
d = pg.query("select name from penny.chart_cat_data where type = 'pic' or type = 'upi' group by name;")
i = 1
for item in d:
  data['income'].append({'name':item['name']})
  income_name_map[item['name']] = i
  i += 1
income_max = i

income_id_map = {}
d = pg.query("select * from penny.chart_cat_data where type = 'pic' or type = 'upi';")
for item in d:
  income_id_map[item['id']] = income_name_map[item['name']]

#transaction_id_map = {}
data['financial_transaction'] = []
d = pg.query("select * from penny.transactions_data order by id;")
i = 1
for item in d:
  status = 2
  if item['verified']:
    status = 5
  f = {'name':item['name'], 'status':status, 'date':item['date'], 'account':account_id_map[item['account']]}
  pg_items = pg.query("select * from penny.items_data where transaction = %i;" % (item['id']))
  items = []
  for t_item in pg_items:
    type = 0
    category = 0
    if t_item['type'] in ('pec', 'upe'):
      type = 1
      category = int(expense_id_map[t_item['category']])+1
    elif t_item['type'] == 'bill':
      type = 2
      category = bill_id_map[t_item['category']]
    elif t_item['type'] == 'savings_e':
      type = 3
      category = saving_id_map[t_item['category']]

    items.append({'name':t_item['title'], 'amount':str(t_item['amount']), 'type':type, 'category':category})
  f['items'] = items

  data['financial_transaction'].append(f)
  #transaction_id_map[item['id']] = i
  i += 1
transactions_max = i

  ##################
d = pg.query("select * from jc.accounts_meta_data;")
i = account_max
for item in d:
  data['account'].append({'balance':str(item['real_balance']), 'name':'jc:%s' % item['name']})
  account_name_map['jc:%s' % item['name']] = i
  i += 1

d = pg.query("select * from jc.accounts_data;")
for item in d:
  account_id_map['jc:%s' % item['id']] = account_name_map['jc:%s' % item['name']] # 31:1

d = pg.query("select name from jc.chart_cat_data where type = 'pec' or type = 'upe' group by name;")
i = expense_max
for item in d:
  data['expense'].append({'name':'jc:%s' % item['name'], 'balance':0, 'minimum':0, 'maximum':0, 'allotment':1})
  expense_name_map['jc:%s' % item['name']] = i
  i += 1

d = pg.query("select * from jc.chart_cat_data where type = 'pec' or type = 'upe';")
for item in d:
  expense_id_map['jc:%s' % item['id']] = expense_name_map['jc:%s' % item['name']]
  t = pg.query("select sum(amount) as total from jc.items_data where category = %i and type in ('pec', 'upe');" % item['id'])
  if t and t[0]['total'] != None:
    total = Decimal(str(t[0]['total']))
    b = Decimal(str(data['expense'][expense_name_map['jc:%s' % item['name']]-1]['balance']))
    data['expense'][expense_name_map['jc:%s' % item['name']]-1]['balance'] = str(b + total)
    data['expense'][expense_name_map['jc:%s' % item['name']]-1]['maximum'] = str(b + total)

d = pg.query("select name from jc.chart_cat_data where type = 'bill' group by name;")
i = bill_max
for item in d:
  data['bill'].append({'name':'jc:%s' % item['name'], 'balance':0, 'maximum':0, 'allotment_date':'2010-11-13', 'repeat_due_date':0, 'due':'2010-11-13'})
  bill_name_map['jc:%s' % item['name']] = i
  i += 1

d = pg.query("select * from jc.chart_cat_data where type = 'bill';")
for item in d:
  bill_id_map['jc:%s' % item['id']] = bill_name_map['jc:%s' % item['name']]
  t = pg.query("select sum(amount) as total from jc.items_data where category = %i and type = 'bill';" % item['id'])
  if t and t[0]['total'] != None:
    total = Decimal(str(t[0]['total']))
    b = Decimal(str(data['bill'][bill_name_map['jc:%s' % item['name']]-1]['balance']))
    data['bill'][bill_name_map['jc:%s' % item['name']]-1]['balance'] = str(b + total)
    data['bill'][bill_name_map['jc:%s' % item['name']]-1]['maximum'] = str(b + total)

d = pg.query("select name from jc.chart_cat_data where type = 'savings_e' group by name;")
i = saving_max
for item in d:
  data['saving'].append({'name':'jc:%s' % item['name'], 'balance':0, 'minimum':0, 'maximum':0, 'allotment_amount':0, 'allotment_date':'2010-11-13', 'repeat_date':0, 'allotment':1})
  saving_name_map['jc:%s' % item['name']] = i
  i += 1

d = pg.query("select * from jc.chart_cat_data where type = 'savings_e';")
for item in d:
  saving_id_map['jc:%s' % item['id']] = saving_name_map['jc:%s' % item['name']]
  t = pg.query("select sum(amount) as total from jc.items_data where category = %i and type = 'savings_e';" % item['id'])
  if t and t[0]['total'] != None:
    total = Decimal(str(t[0]['total']))
    b = Decimal(str(data['saving'][saving_name_map[item['name']]-1]['balance']))
    data['saving'][saving_name_map['jc:%s' % item['name']]-1]['balance'] = str(b + total)
    data['saving'][saving_name_map['jc:%s' % item['name']]-1]['maximum'] = str(b + total)

d = pg.query("select name from jc.chart_cat_data where type = 'pic' or type = 'upi' group by name;")
i = income_max
for item in d:
  data['income'].append({'name':'jc:%s' % item['name']})
  income_name_map['jc:%s' % item['name']] = i
  i += 1

d = pg.query("select * from jc.chart_cat_data where type = 'pic' or type = 'upi';")
for item in d:
  income_id_map['jc:%s' % item['id']] = income_name_map['jc:%s' % item['name']]

#transaction_id_map = {}
d = pg.query("select * from jc.transactions_data order by id;")
i = transactions_max
TRANSACTION_STATUS_ENUM = ['suspect', 'no_receipt', 'receipt', 'scheduled', 'cleared', 'reconciled']
for item in d:
  status = TRANSACTION_STATUS_ENUM.index(item['status'])
  f = {'name':item['name'], 'status':status, 'date':item['date'], 'account':account_id_map['jc:%s' % item['account']]}
  pg_items = pg.query("select * from jc.items_data where transaction = %i;" % (item['id']))
  items = []
  for t_item in pg_items:
    type = 0
    category = 0
    if t_item['type'] in ('pec', 'upe'):
      type = 1
      if 'jc:%s' % t_item['category'] in expense_id_map:
        category = int(expense_id_map['jc:%s' % t_item['category']])+1
    elif t_item['type'] == 'bill':
      type = 2
      category = bill_id_map['jc:%s' % t_item['category']]
    elif t_item['type'] == 'savings_e':
      type = 3
      category = saving_id_map['jc:%s' % t_item['category']]

    items.append({'name':t_item['title'], 'amount':str(t_item['amount']), 'type':type, 'category':category})
  f['items'] = items

  data['financial_transaction'].append(f)
  #transaction_id_map[item['id']] = i
  i += 1

print yaml.safe_dump(data)
