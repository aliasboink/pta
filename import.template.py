#!/usr/bin/env python3
import sys
from os import path
sys.path.insert(0, path.join(path.dirname(__file__)))
from importers.bt import importer as bt
from importers.revolut import importer as revolut
from collections import OrderedDict
from beancount.ingest import extract

bt_debit_dict = OrderedDict([
    ("Example", "Assets:Example"),
    ("Example", "Expenses:Example"),
])
bt_credit_dict = OrderedDict([
    ("Example", "Income:Example"),
])

revolut_debit_dict = OrderedDict([
    (r"\(TRANSFER\) Revolut", "Expenses:Revolut"),
    (r"\(TRANSFER\) To", "Expenses:People"),
    (r"\(EXCHANGE\)", "Expenses:Exchange"),
])
revolut_credit_dict = OrderedDict([
    (r"\(TRANSFER\) Revolut", "Income:Revolut"),
    (r"\(TOPUP\)", "Income:Transfer"),
    (r"\(TRANSFER\) From", "Income:People"),
    (r"\(EXCHANGE\)", "Income:Exchange"),
])

CONFIG = [
    bt.Importer(
      currency="RON",
      bank_account="Assets:Bank:BT",
      debit_dict=bt_debit_dict,
      credit_dict=bt_credit_dict,
    ),
    bt.Importer(
      currency="USD",
      bank_account="Assets:Bank:BT-USD",
      debit_dict=bt_debit_dict,
      credit_dict=bt_credit_dict,
    ),
    revolut.Importer(
      currency="RON",
      bank_account="Assets:Bank:Revolut",
      debit_dict=revolut_debit_dict,
      credit_dict=revolut_credit_dict,
    )
]

extract.HEADER = ';; -*- mode: org; mode: beancount; coding: utf-8; -*-\n'