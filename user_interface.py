
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

import sys

def Property(func):
  """ http://adam.gomaa.us/blog/the-python-property-builtin/ """
  return property(**func())

def sane_raw_input(prompt = "Action: "):
  "Handles EOF more gracefully."

  try:
    res = raw_input(prompt)
  except EOFError:
    res = ""
  return res

class MenuOption(object):
  def __init__(self, letter_command, word_command, description, order=10.0):
    self.letter_command = letter_command[:1]
    self.word_command = word_command.lower()
    self.description = description[:120]
    self.option_match = (self.letter_command.lower(), self.letter_command.upper(), self.word_command)
    self.order = order

  def __call__(self):
    return self.option_match

  def __str__(self):
    """ color string of option """
    return "[ %s ] %s" % (self.letter_command, self.description)

class Interface(object):
  opt_menu = MenuOption('m', 'menu', 'return to main menu', order=19.9)
  opt_quit = MenuOption('q', 'quit', 'quit the program', order=20.0)

  def __init__(self):
    """ add any options that start with opt_ """
    self.menu_options = [getattr(self, x) for x in dir(self) if x[:len('opt_')] == 'opt_']
    self.menu_options.sort(cmp=lambda x, y: cmp(x.order, y.order))

  def get_choice(self):
    "Get menu choice."

    res = sane_raw_input("Enter choice, and press return: ")
    print
    return res

  def get_input(self, prompt):
    "get some input"

    res = sane_raw_input(prompt)
    print
    return res

  def do_quit(self):
    print "Quitting"
    print
    sys.exit(0)

  def handle_interrupt(self, menu_str):
    "Handle a keyboard interrupt exception."

    print "\n\nReceived Ctrl-C or other break signal.\n"
    res = sane_raw_input("Do you want to quit (Y/N)? ")
    print
    res = string.lower(string.strip(res))
    if res in ("y", "yes"):
      do_quit()
    else:
      print "Returning to menu.\n"


  def __call__(self):
    self.show_menu()
    self.handle_response()

  def show_menu(self):
    print
    print "MAIN MENU"
    print
    for opt in self.menu_options:
      print opt
    print

  def handle_response(self):
    res = self.get_choice()

    if res in self.opt_menu():
      print 'show index page'
    elif res in self.opt_quit():
      self.do_quit()

