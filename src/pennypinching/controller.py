import web
import os.path
import httplib
from auth import read_permission, users
from string import Template
from xml.etree.ElementTree import Element, SubElement, tostring
from view import TRANSACTION_STATUS_ENUM
TRANSACTION_STATUS_SYMBOLS_ENUM = ('?', '&larr;', '&rarr;', '&crarr;', '&harr;', '&radic;')
TRANSACTION_STATUS_SYMBOL_MAPPING = dict(zip(TRANSACTION_STATUS_ENUM, TRANSACTION_STATUS_SYMBOLS_ENUM))
TRANSACTION_STATUS_MAPPING = dict(zip(TRANSACTION_STATUS_ENUM, range(0,len(TRANSACTION_STATUS_ENUM))))

class WWW(object):
  def __init__(self):
    super(WWW, self).__init__()
    self.www = 'www'
    #TODO: make the templates to be settable in the app.conf

    self.parts = {}
    for part in dir(self):
      if part[:5] == 'part_':
        self.parts[part[5:]] = getattr(self, part)()

  def _load_static_part(self, part_file):
    part_file_path = os.path.join(os.path.dirname(__file__), self.www, part_file)
    try:
      content = open(part_file_path, 'r').read()
    except IOError, (error, msg):
      content = "Error with '%s': %s, %s" % (part_file_path, error, msg)
    return content

class Page(WWW):
  """ Has nothing to do with books """
  def part_license(self):
    return """
      <p id="license">
        This application is licensed under the
        <a href="https://opensource.org/licenses/agpl-3.0">GNU Affreo General Public License</a>
        <br>
        <a href="https://github.com/jkenlooper/penny-pinching">Source code</a>
        <br>
        <span id="copyright">Copyright &copy; 2010 %s</span>
      </p>
    """ % (self.__author__)


class IndexPage(Page):
  def GET(self):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open(os.path.join(os.path.dirname(__file__), self.www, 'index.html'), 'r').read())
    return template.safe_substitute(**self.parts)

  def part_content(self):
    return self._load_static_part('index_content.html')

  def part_version(self):
    return self.__version__

  def part_login_links(self):
    db_names = set()
    for user in users.keys():
      db_names.add(users[user]['database'])
    div = Element('div', id='login_links')
    h2 = SubElement(div, 'h2')
    h2.text = "Available Databases:"
    for db_name in db_names:
      a = SubElement(div, 'a', href='%s/transactions.html' % db_name)
      a.text = db_name
    return tostring(div)

class TransactionsPage(Page):
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open(os.path.join(os.path.dirname(__file__), self.www, 'transactions.html'), 'r').read())
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
    return tostring(transaction_status_select)


class CategoriesPage(Page):
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open(os.path.join(os.path.dirname(__file__), self.www, 'categories.html'), 'r').read())
    return template.safe_substitute(db_name=db_name,
        currency="$")
