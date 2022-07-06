import srv as srv
import xmltodict
from flask import Flask
from bson import json_util
import json
import re
import pymongo
import pprint
# insall dnsevermodule
import requests
import bson

# Mongodb Connection Code
conn_str = 'mongodb+srv://gowtham:sirasia@cluster0.pudoe.mongodb.net/BankPayments?retryWrites=true&w=majority'
client = pymongo.MongoClient(conn_str, serverSelectionTimeoutMS=4000)
db = client['RulesEngine']
pain_docs = db['Pain Docs']
pain_docs_updated = db['Pain Docs Updated']

# Opening JSON file
app = Flask(__name__)

# returns JSON object as
# a dictionary


@app.route('/getRecords')
def get_records():
    all_records = list(pain_docs.find({}))
    return json.dumps(all_records, default=json_util.default)

def creditor_agent_id_rule():
    pass


def creditor_acct_id_rule(CdtrAcct):
    if not CdtrAcct:
        return False

def debtor_acct_id_rule():
    pass

def bic_Constraint(bic):
    # will be chekced with iban module
    pattern = '[A-Z]{6,6}[a-zA-Z2-9]'
    if re.search(pattern,bic) != None:
        return 1
    else:
        return 0

def iban_Constraint(iban):
    #will be checked with iban module
    pattern = '[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}'

    if re.search(pattern,iban) != None:
        return 1
    else:
        return 0

@app.route('/addModData')
def addModData():
    all_records = pain_docs.find()
    for doc in all_records:
        # new_value = {"new data": "data"}
        # pprint.pprint(doc['Document']['CstmrCdtTrfInitn']['PmtInf']['CdtTrfTxInf'][0].update(new_value))
        # pprint.pprint(doc['Document'].update(newid))
        # pain_docs_updated.insert_one(doc)
        creditor1_bic_score = 0
        creditor1_iban_score = 0
        debtor_bic_score = 0
        debtor_iban_score = 0
        for i in range(1,len(doc)):
            creditor1_iban_score = iban_Constraint(doc['Document']['CstmrCdtTrfInitn']['PmtInf']['CdtTrfTxInf'][i]['CdtrAcct']['Id']['IBAN'])
            creditor1_bic_score =bic_Constraint(doc['Document']['CstmrCdtTrfInitn']['PmtInf']['CdtTrfTxInf'][i]['CdtrAgt']['FinInstnId']['BIC'])
            avg_score = creditor1_iban_score+creditor1_bic_score/2
            doc['Document']['CstmrCdtTrfInitn']['PmtInf']['CdtTrfTxInf'][i]['avg_score'] = avg_score

        debtor_iban_score = iban_Constraint(doc['Document']['CstmrCdtTrfInitn']['PmtInf']['DbtrAcct']['Id']['IBAN'])
        debtor_bic_score = bic_Constraint(doc['Document']['CstmrCdtTrfInitn']['PmtInf']['DbtrAgt']['FinInstnId']['BIC'])
        print(creditor1_iban_score)
        print(creditor1_bic_score)
        print(debtor_iban_score)
        print(debtor_bic_score)
        doc_score: float = (creditor1_iban_score+creditor1_bic_score+debtor_iban_score+debtor_bic_score)/4
        score = doc_score
        doc['Document']['doc_score'] = score
        pprint.pprint(doc)
    return 'yeah, you got it :)'



if __name__ == '__main__':
    app.run()
