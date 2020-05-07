import gspread
from oauth2client.service_account import ServiceAccountCredentials

itemSheet = None
transactionSheet = None

def connect():
    global itemSheet, transactionSheet
    scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json',scope)
    gc = gspread.authorize(credentials)
    wks = gc.open("ItemDB")
    itemSheet = wks.get_worksheet(0)
    transactionSheet = wks.get_worksheet(1)

def append(sheetNum, obj): #Careful for duplicates
    if sheetNum == 0:
        itemSheet.append_row([obj.id, obj.name, obj.members, obj.price, obj.highAlch, obj.buyLimit, obj.noteable, obj.stackable, obj.timestamp])
    elif sheetNum == 1:
        transactionSheet.append_row(["Test2", -1, "true", -1, -1])
    else:
        print ("Invalid sheet (Google Sheet):", sheetNum)

def update(sheetNum, row, col, value):
    if sheetNum == 0:
        itemSheet.update_cell(row, col, value)
    elif sheetNum == 1:
        transactionSheet.update_cell(row, col, value)
    else:
        print ("Invalid sheet (Google Sheet):", sheetNum)
