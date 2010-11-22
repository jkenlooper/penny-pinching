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

import web
import doctest
import yaml
from base64 import b64decode

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
      u['name'] = login
      if db_name == u['database']:
        if password == str(u['password']):
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

