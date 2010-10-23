#! /usr/bin/env python

import web
import doctest
import sys
from view import *
from controller import IndexPage, TransactionsPage, CategoriesPage
status_or = "|".join(TRANSACTION_STATUS_ENUM)
period = "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}\.[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}"
urls = (
    '/', 'IndexPage',
    '/([a-z]+)/transactions\.html', 'TransactionsPage',
    '/([a-z]+)/categories\.html', 'CategoriesPage',
    '/([a-z]+)/user/?', 'UserView', 

    '/([a-z]+)/?', 'DatabaseView', # GET

    '/([a-z]+)/account-list/?', 'AccountListView', # GET
    '/([a-z]+)/account-list-active/?', 'AccountListActiveView', # GET
    '/([a-z]+)/account/?', 'AccountAdd', # POST
    '/([a-z]+)/account/([0-9]+)/?', 'AccountView', # GET
    '/([a-z]+)/account/([0-9]+)/?', 'AccountUpdate', # POST delete attr

    '/([a-z]+)/financial-transaction-list/?', 'FinancialTransactionListView', # GET
    '/([a-z]+)/financial-transaction-list/status/(%s)/?' % status_or, 'FinancialTransactionStatusListView', # GET
    '/([a-z]+)/financial-transaction-list/cleared_suspect/?', 'FinancialTransactionClearedSuspectListView', # GET
    '/([a-z]+)/financial-transaction-list/receipt_no_receipt_scheduled/?', 'FinancialTransactionReceiptNoReceiptScheduledListView', # GET
    '/([a-z]+)/financial-transaction/?', 'FinancialTransactionAdd', # POST
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionView', # GET
    '/([a-z]+)/financial-transaction/([0-9]+)/?', 'FinancialTransactionUpdate', # POST delete attr

    #financial transactions with items
    '/([a-z]+)/financial-transaction-item-list/?', 'FinancialTransactionItemListView', # GET
    '/([a-z]+)/financial-transaction-item/?', 'FinancialTransactionItemAdd', # POST
    '/([a-z]+)/financial-transaction-item/([0-9]+)/?', 'FinancialTransactionItemView', # GET
    '/([a-z]+)/financial-transaction-item/([0-9]+)/?', 'FinancialTransactionItemUpdate', # POST delete attr

    '/([a-z]+)/transaction-item-list/?', 'TransactionItemListView', # GET
    '/([a-z]+)/transaction-item/?', 'TransactionItemAdd', # POST
    '/([a-z]+)/transaction-item/([0-9]+)/?', 'TransactionItemView', # GET
    '/([a-z]+)/transaction-item/([0-9]+)/?', 'TransactionItemUpdate', # POST delete attr

    '/([a-z]+)/expense-list/?', 'ExpenseCategoryListView', # GET
    '/([a-z]+)/expense-list-active/?', 'ExpenseCategoryListActiveView', # GET
    '/([a-z]+)/expense/?', 'ExpenseCategoryAdd', # POST
    '/([a-z]+)/expense/([0-9]+)/?', 'ExpenseCategoryView', # GET
    '/([a-z]+)/expense/([0-9]+)/?', 'ExpenseCategoryUpdate', # POST delete attr

    '/([a-z]+)/bill-list/?', 'BillCategoryListView', # GET
    '/([a-z]+)/bill-list-active/?', 'BillCategoryListActiveView', # GET
    '/([a-z]+)/bill/?', 'BillCategoryAdd', # POST
    '/([a-z]+)/bill/([0-9]+)/?', 'BillCategoryView', # GET
    '/([a-z]+)/bill/([0-9]+)/?', 'BillCategoryUpdate', # POST delete attr

    '/([a-z]+)/saving-list/?', 'SavingCategoryListView', # GET
    '/([a-z]+)/saving-list-active/?', 'SavingCategoryListActiveView', # GET
    '/([a-z]+)/saving/?', 'SavingCategoryAdd', # POST
    '/([a-z]+)/saving/([0-9]+)/?', 'SavingCategoryView', # GET
    '/([a-z]+)/saving/([0-9]+)/?', 'SavingCategoryUpdate', # POST delete attr

    '/([a-z]+)/all-category-list-active/?', 'AllCategoryListActiveView', # GET

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


if __name__ == "__main__":
  if sys.argv[-1] == '--test':
    doctest.testmod()
  elif sys.argv[-1] == '--fcgi':
    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    app.run()
  else:
    app.run()

