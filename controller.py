import web
import json
import os.path
import httplib
from auth import read_permission, users
from string import Template
from xml.etree.ElementTree import Element, SubElement, tostring
from view import TRANSACTION_STATUS_ENUM
TRANSACTION_STATUS_SYMBOLS_ENUM = ('?', '&larr;', '&rarr;', '&crarr;', '&harr;', '&radic;')
TRANSACTION_STATUS_SYMBOL_MAPPING = dict(zip(TRANSACTION_STATUS_ENUM, TRANSACTION_STATUS_SYMBOLS_ENUM))
TRANSACTION_STATUS_MAPPING = dict(zip(TRANSACTION_STATUS_ENUM, range(0,len(TRANSACTION_STATUS_ENUM))))

class IndexPage(object):
  def GET(self):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open('www/index.html', 'r').read())
    content = "This is the index page."
    if os.path.exists('static/index_content.html'):
      content = open('static/index_content.html', 'r').read()
    db_names = set()
    for user in users.keys():
      db_names.add(users[user]['database'])
    print db_names
    login = Element('div', id='login')
    h2 = SubElement(login, 'h2')
    h2.text = "Login"
    for db_name in db_names:
      a = SubElement(login, 'a', href='%s/transactions.html' % db_name)
      a.text = db_name
    return template.safe_substitute(content=content, login=tostring(login))

class TransactionsPage(object):
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open('www/transactions.html', 'r').read())
    return template.safe_substitute(db_name=db_name,
        currency="$",
        transaction_status_select=self.build_transaction_status_select(),
        transaction_status_buttons=self.build_transaction_status_buttons())
    
  def build_transaction_status_buttons(self):
    transaction_status_buttons = Element('div', {'class':'transaction_status'})
    for status in [ x for x in TRANSACTION_STATUS_ENUM if x not in ('reconciled',) ]:
      button = SubElement(transaction_status_buttons, 'span', {'class':'button %s' % status, 'status':str(TRANSACTION_STATUS_MAPPING[status])})
      span = SubElement(button, 'span')
      span.text = TRANSACTION_STATUS_SYMBOL_MAPPING[status]
    return tostring(transaction_status_buttons)
  def build_transaction_status_select(self):
    transaction_status_select = Element('select', {'id':'transaction_status', 'name':'transaction_status'})
    default_status = TRANSACTION_STATUS_ENUM[2]
    for status in [ x for x in TRANSACTION_STATUS_ENUM if x not in ('reconciled',) ]:
      option = SubElement(transaction_status_select, 'option', {'value':str(TRANSACTION_STATUS_ENUM.index(status))})
      if (default_status == status): option.attrib['selected'] = 'selected'
      option.text = status
    print tostring(transaction_status_select)
    return tostring(transaction_status_select)
      

class CategoriesPage(object):
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open('www/categories.html', 'r').read())
    return template.safe_substitute(db_name=db_name,
        currency="$")
