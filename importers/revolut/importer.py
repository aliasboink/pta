import csv
import datetime
import re
import logging
from os import path

from dateutil.parser import parse

from beancount.core.number import D
from beancount.core.number import ZERO
from beancount.core import data
from beancount.core import account
from beancount.core import amount
from beancount.core import position
from beancount.ingest import importer


class Importer(importer.ImporterProtocol):

    def __init__(self, currency, bank_account, debit_dict, credit_dict):
        self.currency = currency
        self.bank_account = bank_account
        self.debit_dict = debit_dict
        self.credit_dict = credit_dict
        self.fees_account = "Expenses:Fees"

    def identify(self, file):
        # Match if the filename is in the specified format
        return re.match(
            r"account-statement_.*.csv",
            path.basename(file.name)
        )

    def file_account(self, _):
        return self.bank_account

    def extract(self, file):
        entries = []
        index = 0
        with open(file.name) as infile:
            for index, row in enumerate(csv.DictReader(infile)):
              meta = data.new_metadata(file.name, index)
              date = parse(row["Completed Date"]).date()
              desc = "({0[Type]}) {0[Description]}".format(row)
              costs = amount.Amount(D(row["Amount"]), self.currency)
              fee = amount.Amount(D(row["Fee"]), self.currency)

              if costs < amount.Amount(D(0), self.currency):

                debit_account = "Expenses:Unknown"
                for vendor, account in self.debit_dict.items():
                    if re.search(vendor, desc, flags=re.IGNORECASE):
                        debit_account = account
                        break
                    
                txn = data.Transaction(
                  meta,
                  date,
                  "*",
                  None,
                  desc,
                  data.EMPTY_SET,
                  data.EMPTY_SET,
                  [
                    data.Posting(debit_account, -costs, None, None, None, None),
                    data.Posting(
                        self.bank_account, costs, None, None, None, None
                    ),
                  ],
                )
              elif costs > amount.Amount(D(0), self.currency):

                credit_account = "Income:Unknown"
                for vendor, account in self.credit_dict.items():
                    if re.search(vendor, desc, flags=re.IGNORECASE):
                        credit_account = account
                        break
                    
                costs_without_fee = amount.sub(costs, fee)

                txn = data.Transaction(
                  meta,
                  date,
                  "*",
                  None,
                  desc,
                  data.EMPTY_SET,
                  data.EMPTY_SET,
                  [
                    data.Posting(self.bank_account, costs_without_fee, None, None, None, None),
                    data.Posting(self.fees_account, fee, None, None, None, None),
                    data.Posting(
                        credit_account, -costs, None, None, None, None
                    ),
                  ],
                )
              else: 
                logging.error("Unexpected transaction.")

              entries.append(txn)


        # Insert a final balance check.
        if index:
            entries.append(
                data.Balance(
                    meta,
                    date + datetime.timedelta(days=1),
                    self.bank_account,
                    amount.Amount(D(row["Balance"]), self.currency),
                    None,
                    None,
                )
            )

        return entries