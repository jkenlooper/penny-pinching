#! /usr/bin/env python
import ConfigParser
from optparse import OptionParser
import urllib2
import urllib
from user_interface import Interface, MenuOption

config = ConfigParser.ConfigParser()
config.read("client.conf")
authenticate = dict(config.items('authenticate'))

password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
top_level_url = "http://%(host)s/%(database)s" % authenticate
password_mgr.add_password(None, top_level_url, authenticate['user'], authenticate['password'])

auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)

opener = urllib2.build_opener(auth_handler)
opener.open(top_level_url)
urllib2.install_opener(opener)

#data = urllib2.urlopen('http://%(host)s/%(database)s/planned-expense/categories' % authenticate)
#print data.read()

class MainInterface(Interface):
  opt_pec = MenuOption('e', 'pec', 'Planned Expense Chart', order=2.0)
  opt_pic = MenuOption('i', 'pic', 'Planned Income Chart', order=2.1)
  opt_bill = MenuOption('b', 'bills', 'Bills', order=2.2)
  opt_savings = MenuOption('s', 'savings', 'Savings Chart', order=2.3)

  opt_accounts = MenuOption('a', 'accounts', 'Accounts', order=3.0)

  opt_add_category = MenuOption('c', 'add_category', 'add a category')
  opt_category_items = MenuOption('h', 'category_items', 'list category items')
  opt_category_item_add = MenuOption('f', 'add_category_item', 'add a category item')
  opt_view_categories = MenuOption('v', 'view', 'view categories')

  def handle_response(self):
    res = self.get_choice()

    if res in self.opt_menu():
      try:
        data = urllib2.urlopen('http://%(host)s/%(database)s' % authenticate)
        print data.read()
      except urllib2.HTTPError, inst:
        print inst
    elif res in self.opt_pec():
      year = self.get_input("year:")
      month = self.get_input("month:")
      d = {'year':year, 'month':month, 'chart_uri':'planned-expense'}
      d.update(authenticate)
      data = urllib2.urlopen('http://%(host)s/%(database)s/%(year)s/%(month)s/%(chart_uri)s' % d) 
      print data.read()
    elif res in self.opt_view_categories():
      year = self.get_input("year:")
      month = self.get_input("month:")
      d = {'year':year, 'month':month, 'chart_uri':'planned-expense'}
      d.update(authenticate)
      data = urllib2.urlopen('http://%(host)s/%(database)s/%(year)s/%(month)s/%(chart_uri)s/categories' % d) 
      print data.read()

    elif res in self.opt_add_category():
      year = self.get_input("year: ")
      month = self.get_input("month: ")
      name = self.get_input("Name of category: ")
      year_month = ""
      if year and month:
        year_month = "%s_%s" % (year, month)
      yaml_string = """
      name: %(name)s
      type: pec
      description: "testing..."
      year_month: %(year_month)s
      active: true
      sum: 0.00
      total: 2.00 
      starting_balance: 0.03
      cap: 0
      rollover: true
      due: 0
      goal_date: 2010-09-23
      goal_total: 0
      """ % {'name': name, 'year_month':year_month}
      encoded_data = urllib.urlencode({'yaml_data_string':yaml_string})
      try:
        response = urllib2.urlopen('http://%(host)s/%(database)s/category' % authenticate, encoded_data)
      except urllib2.HTTPError, inst:
        print inst

    elif res in self.opt_category_item_add():
      title = self.get_input("title of item: ")
      year = self.get_input("year: ")
      month = self.get_input("month: ")
      year_month = ""
      if year and month:
        year_month = "%s_%s" % (year, month)
      yaml_string = """
      title: %(title)s
      amount: 29.93
      description: testing
      cat_data: 16
      year_month: %(year_month)s
      """ % {'title': title, 'year_month':year_month}
      encoded_data = urllib.urlencode({'yaml_data_string':yaml_string})
      try:
        response = urllib2.urlopen('http://%(host)s/%(database)s/category-item' % authenticate, encoded_data)
      except urllib2.HTTPError, inst:
        print inst
    elif res in self.opt_accounts():
      name = self.get_input("name:")
      balance = self.get_input("balance:")
      yaml_string = """
      name: %(name)s
      balance: %(balance)s
      """ % {'name':name, 'balance':balance}
      encoded_data = urllib.urlencode({'yaml_data_string':yaml_string})
      url_data = {'name':name}
      url_data.update(authenticate)
      try:
        response = urllib2.urlopen('http://%(host)s/%(database)s/account' % url_data, encoded_data)
        print response
      except urllib2.HTTPError, inst:
        print inst


    elif res in self.opt_category_items():
      d = {'id':29}
      d.update(authenticate)
      data = urllib2.urlopen('http://%(host)s/%(database)s/category/%(id)s/items/' % d) 
      print data.read()

    elif res in self.opt_quit():
      self.do_quit()

if __name__ == "__main__":
  parser = OptionParser(usage="%%prog ", version="%prog 0.1", description="penny")

  #parser.add_option("--interactive", "-i",
  #    action="store")

  (options, args) = parser.parse_args()
  main = MainInterface()

  while 1:
    try:
      main()
    except KeyboardInterrupt:
      interface.handle_interrupt()
