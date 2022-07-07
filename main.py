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
        cq_present,
        payment_id,
        dq_present,
        daq_iban_present,
        daq_iban_valid):
    return {
        "paymentID": payment_id,
        "Quality": {
          "CreditorAccountQuality": {
            "IBAN_present": caq_iban_present,
            "IBAN_valid": caq_iban_valid
          },
          "CreditorQuality": cq_present,
          "DebtorQuality": dq_present,
          "DebtorAccountQuality": {
              "IBAN_present": daq_iban_present,
              "IBAN_valid": daq_iban_valid
          }
        }
      }
# a dictionary
def message_quality(paymentInfos):
    return {
    "PaymentInfoQuality": paymentInfos
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
def creditor_acct(obj):
    if not obj['CdtrAcct']:
        return False
    else:
        return True

def creditor_acct_id_rule(obj):
    if not obj['CdtrAcct']:
        return False
    else:
        return True



def debtor_rule(obj):
    if not obj['Dbtr']:
        return False
    else:
        return True

def debtor_acct_id_rule(obj):
    if not obj['Id']:
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
        paymentInfo_quality_list = []
        for i in range(len(doc['Document']['CstmrCdtTrfInitn']['PmtInf'])):
            payment_id = doc['Document']['CstmrCdtTrfInitn']['GrpHdr']['MsgId']
            caq_iban_present :int
            caq_iban_valid :int
            cq_present :int
            dq_present :int
            daq_iban_present :int
            daq_iban_valid = int
            if debtor_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]):
                dq_present = 1
            if debtor_acct_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['DbtrAcct']):
                daq_iban_present = 1
                daq_iban_valid = val_IBAN(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['DbtrAcct']['Id']['IBAN'])
            else:
                daq_iban_present = 0
                daq_iban_valid = 0
            for j in range(len(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'])):
                if creditor_acct(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]):
                    cq_present = 1
                    if creditor_acct_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]):
                        caq_iban_present = 1
                        caq_iban_valid = val_IBAN(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]['CdtrAcct']['Id']['IBAN'])
                        print(caq_iban_valid)
                else:
                    cq_present = 0
                    caq_iban_present = 0
            paymentInfo_quality_list.append(update_paymentinfo_quality(caq_iban_present,
                                                                        caq_iban_valid,
                                                                        cq_present,
                                                                        payment_id,
                                                                        dq_present,
                                                                        daq_iban_present,
                                                                        daq_iban_valid))
        doc['Document']['MessageQuality'] =  message_quality(paymentInfo_quality_list)

        pprint.pprint(doc)
    return 'yeah, you got it :)'



if __name__ == '__main__':
    app.run()
