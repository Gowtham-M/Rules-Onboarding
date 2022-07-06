# import srv as srv
# import xmltodict
from flask import Flask
from bson import json_util
import json
import re
import pymongo
import pprint
import schwifty
# insall dnspython
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


def update_paymentinfo_quality(
        caq_iban_present,
        caq_iban_valid,
        cq_iban_present,
        payment_id,
        dq_iban_present,
        daq_iban_present,
        daq_iban_valid):
    return {
        "paymentID": payment_id,
        "Quality": {
          "CreditorAccountQuality": {
            "IBAN_present": caq_iban_present,
            "IBAN_valid": caq_iban_valid
          },
          "CreditorQuality": {
            "IBAN_present": cq_iban_present
          },
          "DebtorQuality": {
              "IBAN_present": dq_iban_present
          },
          "DebtorAccountQuality": {
              "IBAN_present": daq_iban_present,
              "IBAN_valid": daq_iban_valid
          }
        }
      }
# a dictionary
def message_quality(paymentInfos):
    return {
  "MessageQuality": {
    "PaymentInfoQuality": paymentInfos
  }
}

@app.route('/getRecords')
def get_records():
    all_records = list(pain_docs.find({}))
    return json.dumps(all_records, default=json_util.default)


def creditor_agent_id_rule(obj):
    if not obj['CdtrAgt']:
        return False
    else:
        return True


def creditor_acct_id_rule(obj):
    if not obj['CdtrAcct']:
        return False
    else:
        return True

def debtor_acct_id_rule(obj):
    if not obj['DbtrAcct']:
        return False
    else:
        return True


def val_IBAN(iban_no):
    try:
        if(schwifty.IBAN.validate(schwifty.IBAN(iban_no))):
            return 1
        else:
            return 0
    except:
        return 0

#will be checked with iban module
def val_BIC(bic_no):
    try:
        if(schwifty.BIC.validate(schwifty.BIC(bic_no))):
            return 1
        else:
            return 0
    except:
        return 0

@app.route('/addModData')
def addModData():
    all_records = pain_docs.find()
    for doc in all_records:
        creditor_scores = []
        for i in range(len(doc['Document']['CstmrCdtTrfInitn']['PmtInf'])):
            if debtor_acct_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]):

                for j in range(len(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'])):
                    if creditor_agent_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]) and creditor_acct_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]):
                        crdtr_bicscore = val_BIC(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]['CdtrAgt']['FinInstnId']['BIC'])
                        crdtr_ibanscore = val_IBAN(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]['CdtrAcct']['Id']['IBAN'])
                        print(crdtr_ibanscore)
                        print(crdtr_bicscore)
                        avg_score =  crdtr_bicscore+crdtr_ibanscore/2
                    doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]['avg_score'] = avg_score
                    creditor_scores.append(avg_score)
                    print(creditor_scores)

            debtor_iban_score = val_IBAN(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['DbtrAcct']['Id']['IBAN'])
            debtor_bic_score = val_BIC(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['DbtrAgt']['FinInstnId']['BIC'])
            quality_score: float = (sum(creditor_scores)+debtor_bic_score+debtor_iban_score)/7
            doc['Document']['QualityScore'] = quality_score
        pprint.pprint(doc)
    return 'yeah, you got it :)'



if __name__ == '__main__':
    app.run()
