#! /usr/bin/env python

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
        if password == u['password']:
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

