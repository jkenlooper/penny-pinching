#! /usr/bin/env python
import ConfigParser
from optparse import OptionParser
import urllib2
import urllib
import yaml
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

  opt_account_add = MenuOption('a', 'accounts', 'Add an Account', order=3.0)
  opt_account_update = MenuOption('u', 'updateaccounts', 'Update an Account', order=3.1)
  opt_account_list = MenuOption('l', 'accounts', 'list accounrs', order=3.2)

  opt_add_transaction = MenuOption('t', 'transaction', 'add a financial transaction', order=4.0)

  opt_add_category = MenuOption('c', 'add_category', 'add a category')
  opt_category_items = MenuOption('h', 'category_items', 'list category items')
  opt_expense_category_add = MenuOption('f', 'add_category_item', 'add an expense category')
  opt_expense_category_list = MenuOption('v', 'view', 'view expense categories')

  opt_period_test = MenuOption('p', 'period', 'view period test')
  opt_init_data = MenuOption('d', 'data', 'initialize with test data', order=8.0)

  def add(self, k, path):
    s = self.get_input("%s: " % ", ".join(k))
    url_data = authenticate
    url_data['path'] = path
    if s != '':
      user_input = dict(zip(k, s.split(',')))
    yaml_string = yaml.safe_dump(user_input)
    encoded_data = urllib.urlencode({'data_string':yaml_string})
    try:
      response = urllib2.urlopen('http://%(host)s/%(database)s/%(path)s/' % url_data, encoded_data)
    except urllib2.HTTPError, inst:
      print inst

  def handle_response(self):
    res = self.get_choice()

    if res in self.opt_menu():
      try:
        data = urllib2.urlopen('http://%(host)s/%(database)s' % authenticate)
        print data.read()
      except urllib2.HTTPError, inst:
        print inst
    elif res in self.opt_init_data():
      d = """
      account:
        -
          name: checking
          balance: 89.21
        -
          name: savings
          balance: 289.21
      financial_transaction:
        -
          name: smiths
          status: 1
          date: 2010-09-28
          account: 1
          items:
            -
              name: food
              amount: 23.92
              type: 1
              category: 2
            -
              name: rocks
              amount: 3.92
              type: 1
              category: 3

              
        -
          name: smiths
          status: 2
          date: 2010-09-18
          account: 1
          items:
            -
              name: sandwiches
              amount: 2.10
              type: 1
              category: 2
            -
              name: pebbles
              amount: 33.92
              type: 1
              category: 3
        -
          name: albertsons
          status: 1
          date: 2010-08-18
          account: 1
          items:
            -
              name: cookies
              amount: 22.10
              type: 1
              category: 2
            -
              name: sand
              amount: 10.92
              type: 1
              category: 3
      expense:
        -
          name: groceries
          balance: 300
          active: true
          cap: 600.23
          allotment: 50
        -
          name: other
          balance: 100
          active: true
          cap: 200.23
          allotment: 20
      bill:
      saving:
      """
      data = yaml.safe_load(d)
      try:
        all = urllib2.urlopen('http://%(host)s/%(database)s' % authenticate)
        print all.read()
      except urllib2.HTTPError, inst:
        print inst

      for account in data['account']:
        encoded_data = urllib.urlencode({'data_string':yaml.safe_dump(account)})
        try:
          response = urllib2.urlopen('http://%(host)s/%(database)s/account/' % authenticate, encoded_data)
        except urllib2.HTTPError, inst:
          print inst
      for expense in data['expense']:
        encoded_data = urllib.urlencode({'data_string':yaml.safe_dump(expense)})
        try:
          response = urllib2.urlopen('http://%(host)s/%(database)s/expense/' % authenticate, encoded_data)
        except urllib2.HTTPError, inst:
          print inst
      if data['bill']:
        for bill in data['bill']:
          encoded_data = urllib.urlencode({'data_string':yaml.safe_dump(bill)})
          try:
            response = urllib2.urlopen('http://%(host)s/%(database)s/bill/' % authenticate, encoded_data)
          except urllib2.HTTPError, inst:
            print inst
      if data['saving']:
        for saving in data['saving']:
          encoded_data = urllib.urlencode({'data_string':yaml.safe_dump(saving)})
          try:
            response = urllib2.urlopen('http://%(host)s/%(database)s/saving/' % authenticate, encoded_data)
          except urllib2.HTTPError, inst:
            print inst
      for financial_transaction in data['financial_transaction']:
        encoded_data = urllib.urlencode({'data_string':yaml.safe_dump(financial_transaction)})
        try:
          response = urllib2.urlopen('http://%(host)s/%(database)s/financial-transaction-item/' % authenticate, encoded_data)
        except urllib2.HTTPError, inst:
          print inst

       
          
      
    elif res in self.opt_add_transaction():
      def get_items():
        items = []
        done = False
        print "item format: name, amount, type, category "
        while not done:
          k = ('name', 'amount', 'type', 'category')
          s = self.get_input("item: ")
          if s == '':
            done = True
          else:
            items.append(dict(zip(k, s.split(','))))
        return items
      user_input = {
          'name': self.get_input("name: "),
          'status': self.get_input("status: "),
          'date': self.get_input("date: "),
          'account': self.get_input("account: "),
          'items': get_items(),
          }

      yaml_string = yaml.safe_dump(user_input)
      encoded_data = urllib.urlencode({'data_string':yaml_string})
      try:
        response = urllib2.urlopen('http://%(host)s/%(database)s/financial-transaction-item/' % authenticate, encoded_data)
      except urllib2.HTTPError, inst:
        print inst

    elif res in self.opt_account_list():
      data = urllib2.urlopen('http://%(host)s/%(database)s/account-list-active/' % authenticate) 
      print data.read()

    elif res in self.opt_expense_category_list():
      data = urllib2.urlopen('http://%(host)s/%(database)s/expense-list/' % authenticate) 
      print data.read()

    elif res in self.opt_expense_category_add():
      k = ('name', 'balance', 'active', 'cap', 'allotment')
      s = self.get_input("%s: " % ", ".join(k))
      if s != '':
        user_input = dict(zip(k, s.split(',')))
      yaml_string = yaml.safe_dump(user_input)
      encoded_data = urllib.urlencode({'data_string':yaml_string})
      try:
        response = urllib2.urlopen('http://%(host)s/%(database)s/expense' % authenticate, encoded_data)
      except urllib2.HTTPError, inst:
        print inst

    elif res in self.opt_period_test():
      data = urllib2.urlopen('http://%(host)s/%(database)s/period/2010-5-25.2010-10-10/financial-transaction-list/' % authenticate) 
      print data.read()

    elif res in self.opt_account_add():
      self.add(('name', 'balance'), 'account')

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
