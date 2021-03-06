#! /usr/bin/env python

import web
import doctest
import sys
from view import *
from controller import Page, IndexPage, TransactionsPage, CategoriesPage

import _version

#TODO: better way of doing this?
Page.__version__ = _version.__version__
Page.__author__ = _version.__author__

status_or = "|".join(TRANSACTION_STATUS_ENUM)
period = "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}\.[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}"
urls = (
    '/', 'IndexPage',
    '/([a-z]+)/transactions\.html', 'TransactionsPage',
    '/([a-z]+)/categories\.html', 'CategoriesPage',
    '/([a-z]+)/user/?', 'UserView',

    '/([a-z]+)/?', 'DatabaseView', # GET
    '/([a-z]+)/init/?', 'DatabaseInitialize', # GET

    '/([a-z]+)/account-list/?', 'AccountListView', # GET
    '/([a-z]+)/account-list-active/?', 'AccountListActiveView', # GET
    '/([a-z]+)/account/?', 'AccountAdd', # POST
    '/([a-z]+)/account/([0-9]+)/?', 'AccountView', # GET
    '/([a-z]+)/account/([0-9]+)/update/?', 'AccountUpdate', # POST delete attr
    '/([a-z]+)/account/([0-9]+)/activate/?', 'AccountActivate',

    '/([a-z]+)/account/([0-9]+)/cleared-to-reconciled/?', 'ClearedToReconciledUpdate', # POST

    '/([a-z]+)/financial-transaction-list/?', 'FinancialTransactionListView', # GET
    '/([a-z]+)/financial-transaction-list/status/(%s)/?' % status_or, 'FinancialTransactionStatusListView', # GET
    '/([a-z]+)/financial-transaction-list/period/(%s)/status/(%s)/?' % (period, status_or), 'FinancialTransactionPeriodStatusListView', # GET
    '/([a-z]+)/financial-transaction-list/cleared_suspect/?', 'FinancialTransactionClearedSuspectListView', # GET
    '/([a-z]+)/financial-transaction-list/receipt_no_receipt_scheduled/?', 'FinancialTransactionReceiptNoReceiptScheduledListView', # GET
    '/([a-z]+)/financial-transaction/?', 'FinancialTransactionAdd', # POST
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionView', # GET
    '/([a-z]+)/financial-transaction/([0-9]+)/update/?', 'FinancialTransactionUpdate', # POST delete attr
    '/([a-z]+)/financial-transaction-status/([0-9]+)/?', 'FinancialTransactionStatusUpdate',

    #financial transactions with items
    '/([a-z]+)/financial-transaction-item-list/?', 'FinancialTransactionItemListView', # GET
    '/([a-z]+)/financial-transaction-item/?', 'FinancialTransactionItemAdd', # POST
    '/([a-z]+)/financial-transaction-item/([0-9]+)/?', 'FinancialTransactionItemView', # GET
    '/([a-z]+)/financial-transaction-item/([0-9]+)/update/?', 'FinancialTransactionItemUpdate',
    '/([a-z]+)/financial-transaction-item/([0-9]+)/delete/?', 'FinancialTransactionItemDelete',

    '/([a-z]+)/transaction-item-list/?', 'TransactionItemListView', # GET
    '/([a-z]+)/transaction-item/?', 'TransactionItemAdd', # POST
    '/([a-z]+)/transaction-item/([0-9]+)/?', 'TransactionItemView', # GET
    '/([a-z]+)/transaction-item/([0-9]+)/?', 'TransactionItemUpdate', # POST delete attr

    '/([a-z]+)/setting/([a-z_]+)/?', 'SettingView',
    '/([a-z]+)/setting/([a-z_]+)/update/?', 'SettingUpdate',

    '/([a-z]+)/expense-list/?', 'ExpenseCategoryListView', # GET
    '/([a-z]+)/expense-list-active/?', 'ExpenseCategoryListActiveView', # GET
    '/([a-z]+)/expense-list-inactive/?', 'ExpenseCategoryListInActiveView', # GET
    '/([a-z]+)/expense/?', 'ExpenseCategoryAdd', # POST
    '/([a-z]+)/expense/([0-9]+)/?', 'ExpenseCategoryView', # GET
    '/([a-z]+)/expense/([0-9]+)/update/?', 'ExpenseCategoryUpdate',
    '/([a-z]+)/expense-balance/([0-9]+)/?', 'ExpenseCategoryUpdateBalance',
    '/([a-z]+)/expense-active/([0-9]+)/?', 'ExpenseCategoryUpdateActive',

    '/([a-z]+)/bill-list/?', 'BillCategoryListView', # GET
    '/([a-z]+)/bill-list-active/?', 'BillCategoryListActiveView', # GET
    '/([a-z]+)/bill-list-inactive/?', 'BillCategoryListInActiveView', # GET
    '/([a-z]+)/bill/?', 'BillCategoryAdd', # POST
    '/([a-z]+)/bill/([0-9]+)/?', 'BillCategoryView', # GET
    '/([a-z]+)/bill/([0-9]+)/update/?', 'BillCategoryUpdate',
    '/([a-z]+)/bill-active/([0-9]+)/?', 'BillCategoryUpdateActive',

    '/([a-z]+)/saving-list/?', 'SavingCategoryListView', # GET
    '/([a-z]+)/saving-list-active/?', 'SavingCategoryListActiveView', # GET
    '/([a-z]+)/saving-list-inactive/?', 'SavingCategoryListInActiveView', # GET
    '/([a-z]+)/saving/?', 'SavingCategoryAdd', # POST
    '/([a-z]+)/saving/([0-9]+)/?', 'SavingCategoryView', # GET
    '/([a-z]+)/saving/([0-9]+)/update/?', 'SavingCategoryUpdate',
    '/([a-z]+)/saving-active/([0-9]+)/?', 'SavingCategoryUpdateActive',

    '/([a-z]+)/all-category-list/?', 'AllCategoryListView', # GET
    '/([a-z]+)/all-category-list-active/?', 'AllCategoryListActiveView', # GET

    '/([a-z]+)/total-balance/?', 'TotalBalanceView',

    '/([a-z]+)/period/(%s)/financial-transaction-list/?' % (period), 'PeriodFinancialTransactionListView', # GET
    '/([a-z]+)/period/(%s)/financial-transaction-item-list/?' % (period), 'PeriodFinancialTransactionItemListView', # GET
    '/([a-z]+)/period/(%s)/financial-transaction-list/account/([0-9]+)/?' % (period), 'PeriodFinancialTransactionAccountListView', # GET
    '/([a-z]+)/period/(%s)/financial-transaction-item-list/account/([0-9]+)/?' % (period), 'PeriodFinancialTransactionItemAccountListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/?' % (period), 'PeriodTransactionItemListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/expense/?' % (period), 'PeriodTransactionItemExpenseListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/expense/([0-9]+)/?' % (period), 'PeriodTransactionItemExpenseCategoryListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/bill/?' % (period), 'PeriodTransactionItemBillListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/bill/([0-9]+)/?' % (period), 'PeriodTransactionItemBillCategoryListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/saving/?' % (period), 'PeriodTransactionItemSavingListView', # GET
    '/([a-z]+)/period/(%s)/transaction-item-list/saving/([0-9]+)/?' % (period), 'PeriodTransactionItemSavingCategoryListView', # GET

    )

app = web.application(urls, globals())
web.config.debug = True

def set_yaml_content():
  web.header('Content-type', "text/yaml; charset=utf-8")

app.add_processor(web.loadhook(set_yaml_content))

def run():
  app.run()

def start():
  """ setup for running in wsgi """
  web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
  app.run()

def stop():
  """ Oh, no!!!  No brakes!!!"""
  pass

def main():
  "first arg is the port, second is command"
  if sys.argv[2] == 'run':
    run()
  elif sys.argv[2] == 'start':
    start()
  elif sys.argv[2] == 'stop':
    stop()

if __name__ == "__main__":
  if sys.argv[-1] == '--test':
    doctest.testmod()
  elif sys.argv[-1] == '--localhost':
    app.run()
  else:
    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    app.run()

