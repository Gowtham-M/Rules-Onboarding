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


# def update_paymentinfo_quality(
#         caq_iban_present,
#         caq_iban_valid,
#         cq_present,
#         payment_id,
#         dq_present,
#         daq_iban_present,
#         daq_iban_valid):
#     return {
#         "paymentID": payment_id,
#         "Quality": {
#           "CreditorAccountQuality": {
#             "IBAN_present": caq_iban_present,
#             "IBAN_valid": caq_iban_valid
#           },
#           "CreditorQuality": cq_present,
#           "DebtorQuality": dq_present,
#           "DebtorAccountQuality": {
#               "IBAN_present": daq_iban_present,
#               "IBAN_valid": daq_iban_valid
#           }
#         }
#       }

def creditor_quality(
        caq_iban_present,
        caq_iban_valid,
        cq_present):
    return {
          "CreditorAccountQuality": {
            "IBAN_present": caq_iban_present,
            "IBAN_valid": caq_iban_valid
          },
          "CreditorQuality": cq_present,
          }

def debtor_quality(cdtr_list,dq_present,daq_iban_present,daq_iban_valid):
    return {
          "crdtr_list":cdtr_list,
          "DebtorAccountQuality": {
            "IBAN_present": daq_iban_present,
            "IBAN_valid": daq_iban_valid
          },
          "DebtorQuality": dq_present,
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
        return 0
    else:
        return 1
def creditor_acct(obj):
    if not obj['CdtrAcct']:
        return 0
    else:
        return 1

def creditor_acct_id_rule(obj):
    if not obj['CdtrAcct']:
        return 0
    else:
        return 1



def debtor_rule(obj):
    if not obj['Dbtr']:
        return 0
    else:
        return 1

def debtor_acct_id_rule(obj):
    if not obj['Id']:
        return 0
    else:
        return 1


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
        paymentInfo_quality = {}
        for i in range(len(doc['Document']['CstmrCdtTrfInitn']['PmtInf'])):
            dq_present =  debtor_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i])
            daq_iban_present = debtor_acct_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['DbtrAcct'])
            daq_iban_valid = val_IBAN(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['DbtrAcct']['Id']['IBAN'])
            # debtor_dict = debtor_quality(dq_present,daq_iban_present,daq_iban_valid)
            crdtr_list = []
            for j in range(len(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'])):
                dict = {}
                cq_present =creditor_acct(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j])
                caq_iban_present = creditor_acct_id_rule(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j])
                caq_iban_valid = val_IBAN(doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]['CdtrAcct']['Id']['IBAN'])
                data = creditor_quality(cq_present,caq_iban_present,caq_iban_valid)
                dict[doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['CdtTrfTxInf'][j]['PmtId']['EndToEndId']] = data
                crdtr_list.append(dict)

            paymentInfo_quality[doc['Document']['CstmrCdtTrfInitn']['PmtInf'][i]['PmtInfId']]= debtor_quality(crdtr_list,dq_present,daq_iban_present,daq_iban_valid)
            pprint.pprint(paymentInfo_quality)
        doc['Document']['quality_dict']= paymentInfo_quality
        # pain_docs_updated.insert_one(doc)
        pprint.pprint(doc)
    return json.dumps(doc, default=json_util.default)



if __name__ == '__main__':
    app.run()

# caq_iban_present :int
# caq_iban_valid :int
# cq_present :int
# dq_present :int
# daq_iban_present :int
# daq_iban_valid = int