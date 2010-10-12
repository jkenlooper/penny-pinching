import web
import os.path
import httplib
from auth import read_permission
from string import Template
from xml.etree.ElementTree import Element, SubElement, tostring

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
    #add_transaction_box = 
    return template.safe_substitute()

class CategoriesPage(object):
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open('www/categories.html', 'r').read())
    return template.safe_substitute()
