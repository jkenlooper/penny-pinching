
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
    part_file_path = os.path.join(self.www, part_file)
    try:
      content = open(part_file_path, 'r').read()
    except IOError, (error, msg):
      content = "Error with '%s': %s, %s" % (part_file_path, error, msg)
    return content

class IndexPage(WWW):
  def GET(self):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open(os.path.join(self.www, 'index.html'), 'r').read())
    return template.safe_substitute(**self.parts)

  def part_content(self):
    return self._load_static_part('index_content.html')

  def part_login_links(self):
    db_names = set()
    for user in users.keys():
      db_names.add(users[user]['database'])
    div = Element('div', id='login_links')
    h2 = SubElement(div, 'h2')
    h2.text = "Login"
    for db_name in db_names:
      a = SubElement(div, 'a', href='%s/transactions.html' % db_name)
      a.text = db_name
    return tostring(div)

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
    return tostring(transaction_status_select)
      

class CategoriesPage(object):
  @read_permission
  def GET(self, db_name, _user=None):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open('www/categories.html', 'r').read())
    return template.safe_substitute(db_name=db_name,
        currency="$")

class SourceIndexPage(object):
  def GET(self):
    web.redirect("/source/site.py")

class SourcePage(WWW):
  public_viewable_source_files = (
      'auth.py',
      'client.py',
      'controller.py',
      'conversion.py',
      'site.py',
      'user_interface.py',
      'view.py',
      )
  #TODO: show the source with syntax hilighting
  def GET(self, python_file):
    web.header('Content-type', "text/html; charset=utf-8")
    template = Template(open(os.path.join(self.www, 'source.html'), 'r').read())
    return template.safe_substitute(source=self.source(python_file), **self.parts)

  def part_header(self):
    return self._load_static_part('source_header.html')

  def part_content(self):
    return self._load_static_part('source_content.html')

  def part_source_files_list(self):
    ul = Element('ul')
    for f in self.public_viewable_source_files:
      li = SubElement(ul, 'li')
      a = SubElement(li, 'a', href='/source/%s' % f)
      a.text = f
    return tostring(ul)

  def source(self, python_file):
    if python_file in self.public_viewable_source_files:
      try:
        content = open(python_file, 'r').read()
      except IOError, (error, msg):
        content = "Error with '%s': %s, %s" % (python_file, error, msg)
      return content
    else:
      return "No access to that file"
