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

    def identify(self, file):
        # Match if the filename is in the specified format
        return re.match(
            r"RO\d{2}BTRLRONCRT\d+-\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4}\.csv",
            path.basename(file.name)
        )
    
    def file_account(self, _):
        return self.bank_account

    def extract(self, file):
        entries = []
        index = 0
        final_sum = amount.Amount(D(0), self.currency)
        final_date = datetime.MAXYEAR
        with open(file.name) as infile:
            for _ in range(14):
                next(infile)
            for index, row in enumerate(csv.DictReader(infile)):
                if index == 0:
                    final_sum = amount.Amount(D(row["Suma"]), self.currency)
                    final_date = parse(row["Data tranzac?iei"], dayfirst=True).date()
                meta = data.new_metadata(file.name, index)
                date = parse(row["Data tranzac?iei"], dayfirst=True).date()
                desc = row["Descriere"]
                debit = amount.Amount(D(row["Debit"]), self.currency)
                credit = amount.Amount(D(row["Credit"]), self.currency)
                link = row["Referinta tranzactiei"]

                # If credit is 0, it means it's a DEBIT (outflow) transaction.
                if credit == amount.Amount(D(0), self.currency):

                    debit_account = "Expenses:Unknown"
                    for vendor, account in self.debit_dict.items():
                        if re.search(vendor, desc):
                            debit_account = account
                            break

                    txn = data.Transaction(
                    meta,
                    date,
                    "*",
                    None,
                    desc,
                    data.EMPTY_SET,
                    {link},
                    [
                        data.Posting(debit_account, debit, None, None, None, None),
                        data.Posting(
                            self.bank_account, -debit, None, None, None, None
                        ),
                    ],
                    )
                # If debit is 0, it means it's a CREDIT (inflow) transaction.
                elif debit == amount.Amount(D(0), self.currency):

                    credit_account = "Income:Unknown"
                    for vendor, account in self.credit_dict.items():
                        if re.search(vendor, desc):
                            credit_account = account
                            break

                    txn = data.Transaction(
                    meta,
                    date,
                    "*",
                    None,
                    desc,
                    data.EMPTY_SET,
                    {link},
                    [
                        data.Posting(self.bank_account, credit, None, None, None, None),
                        data.Posting(
                            credit_account, -credit, None, None, None, None
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
                    final_date + datetime.timedelta(days=1),
                    self.bank_account,
                    final_sum,
                    None,
                    None,
                )
            )

        return entries