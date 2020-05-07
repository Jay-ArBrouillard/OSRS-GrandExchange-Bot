import requests
import json
import ijson
import win32gui
from win32api import GetSystemMetrics
from PIL import ImageGrab
import cv2
import numpy as np
import time
import pytesseract
import pyautogui
import math
import random
from enum import Enum
from urllib.request import urlopen
import database as db
from GEItem import GEItem
from bs4 import BeautifulSoup
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Status(Enum):
    buyingMargin = 1
    sellingMargin = 2
    buying = 3
    selling = 4
    onCooldown = 5
    available = 6

#Webscrape GE-Tracker website to get rest of item ids not in itemId.json
def findItemIdsFromGETracker():
    db.connect()
    idNum = 0 #highest id is 23754
    errorCount = 0
    while idNum < 23755:
        try:
            print("Checking idNum", idNum)
            r = requests.get("http://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item=%s" % str(idNum))
            time.sleep(2)
            r.raise_for_status()
            json = r.json()
            if r.status_code == 200 and json != None:
                id = json['item']['id']
                name = json['item']['name']
                cell = db.itemSheet.find(name)
                if id and name and cell:
                    print("Updating %s with id %d" % (name, id))
                    db.update(0, cell.row, 1, id)
                    errorCount = 0
            idNum = idNum + 1
        except Exception as e:
            if errorCount == 3:
                idNum = idNum + 1
                errorCount = 0
            errorCount = errorCount + 1

def findGameWindow(name):
	try:
		return win32gui.FindWindow(None, name)
	except:
		print("the game isn't open.")
		exit(0)

def getWindowRect(hwnd):
    x0, y0, x1, y1 = win32gui.GetWindowRect(hwnd)
    w = x1 - x0 # width
    h = y1 - y0 # height
    w = w + (1050 - w) # set width to 1000
    h = h + (800 - h) # set height to 800
    center_width = int(GetSystemMetrics(0)/3)
    center_width = center_width + (GetSystemMetrics(0) - (int(GetSystemMetrics(0)/3) + 1050))-100
    center_height = int(GetSystemMetrics(1)/3)
    center_height = center_height + (GetSystemMetrics(1) - (int(GetSystemMetrics(1)/3) + 800))-100
    win32gui.MoveWindow(hwnd, center_width, center_height, w, h, True)
    return win32gui.GetWindowRect(hwnd)

def hideWindow(hwnd):
	win32gui.ShowWindow(hwnd, 0)

def showWindow(hwnd):
	win32gui.ShowWindow(hwnd, 1)

def setActiveWindow(hwnd):
	win32gui.SetForegroundWindow(hwnd)

def captureScreen(screen):
    return ImageGrab.grab(bbox=(screen[0]+10, screen[1]+30, screen[2]-10, screen[3]-10))

def image_to_text(im, isNumber):
    scale_percent = 200
    #calculate the 50 percent of original dimensions
    width = int(im.shape[1] * (scale_percent / 100 + 1))
    height = int(im.shape[0] * (scale_percent / 100 + 1))
    # dsize
    dsize = (width, height)
    # resize image
    im = cv2.resize(im, dsize)
    # convert color image to grayscale
    grayscale_image = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    # Otsu Tresholding method find perfect treshold, return an image with only black and white pixels
    _, binary_image = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_OTSU)

    # we just don't know if the text is in black and background in white or vice-versa
    # so we count how many black pixels and white pixels there are
    count_white = np.sum(binary_image > 0)
    count_black = np.sum(binary_image == 0)

    # if there are more black pixels than whites, then it's the background that is black so we invert the image's color
    if count_black > count_white:
        binary_image = 255 - binary_image

    black_text_white_background_image = binary_image
    cv2.imshow("img", black_text_white_background_image)
    cv2.waitKey()
    cv2.destroyAllWindows()
    if isNumber:
        text = pytesseract.image_to_string(black_text_white_background_image, lang='eng', config='-c tessedit_char_whitelist=0123456789').strip()
        if not text and not text.isnumeric():
            print("here")
            print(pytesseract.image_to_string(im, lang='eng', config='-c tessedit_char_whitelist=0123456789').strip())
            return pytesseract.image_to_string(im, lang='eng', config='-c tessedit_char_whitelist=0123456789').strip()
        else:
            print (text)
            return text
    else:
        text = pytesseract.image_to_string(black_text_white_background_image, lang='eng').strip()
        if not text and text not in data_dict and text != 'Buy' and text != 'Empty' and text != 'Sell':
            return pytesseract.image_to_string(im, lang='eng').strip()
        else:
            return text
        

def get_price_from_api(item_id):
    print("Entering get_price_from_api:", item_id)
    try:
        r = requests.get("http://services.runescape.com/m=itemdb_oldschool/api/catalogue/detail.json?item=%s" % str(item_id))
        r.raise_for_status()
        if r.status_code == 200:
            json = r.json()
            return json['item']['current']['price'] #Returned in ge format: 112K, 14.3M
        else:
            return -1
    except Exception as e:
        return -1

def getItemIdFromFile(itemName):
    try:
        with open('itemId.json') as json_file:
            data = json.load(json_file)
            for obj in data:
                if obj['name'] == itemName:
                    return obj['id']
            return -1
    except Exception as e:
        return -1

#Webscrape for every OSRS item and their buy limit then get item ids and add to google sheet
# def initialize_pickle_file():
#     print("Getting items, Buy limitings, and item ids...")
#     parser = ijson.parse(urlopen('https://www.osrsbox.com/osrsbox-db/items-complete.json'))

#     index = -1
#     id = ".id"
#     nameStr = ".name"
#     membersStr = ".members"
#     tradeableGeStr = ".tradeable_on_ge"
#     stackableStr = ".stackable"
#     noteableStr = ".noteable"
#     costStr = ".cost"
#     highAlchStr = ".highalch"
#     buyLimitStr = ".buy_limit"
#     db.connect()
#     item = GEItem()
#     seen = set()
#     for prefix, event, value in parser:
#         if not prefix and event and event == 'map_key' and value and value != None:
#             index = value
#         else:
#             #item_id, buy_limit, status.ENUM, last_price_bought, last_quantity_bought, buy_offer_in_seconds, buy_offer_done_seconds, sell_offer_in_seconds, sell_offer_out_seconds, profit, elapsed_time_hours
#             if value == None:
#                 continue
#             if str(index)+nameStr in prefix:
#                 item.name = value.strip()
#             elif str(index)+membersStr in prefix:
#                 item.members = bool(value)
#             elif str(index)+tradeableGeStr in prefix:
#                 item.tradeable_on_ge = bool(value)
#             elif str(index)+stackableStr in prefix:
#                 item.stackable = bool(value)
#             elif str(index)+noteableStr in prefix:
#                 item.noteable = bool(value)
#             elif str(index)+costStr in prefix: #The price value is outdated from static json file
#                 item.price = int(value)
#             elif str(index)+highAlchStr in prefix:
#                 item.highAlch = int(value)
#             elif str(index)+buyLimitStr in prefix:
#                 item.buyLimit = int(value)
#                 if item.tradeable_on_ge == True and item.name and item.name not in seen:
#                     seen.add(item.name)
#                     item.id = getItemIdFromFile(item.name)
#                     item.timestamp = time.ctime()
#                     db.append(0, item) #Add to google sheet database
#                     item = GEItem()
#                     time.sleep(1) #We need this to prevent API 429 Error (1 request per sec)

def ge_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.1f%s' % (num, ['', 'k', 'm', 'b'][magnitude])

def buy(slot):
    pyautogui.click(x=slot[0][0]+20, y=slot[0][1]+100, clicks=1, interval=0, button='left') #Click to set up offer
    time.sleep(1)
    pyautogui.typewrite('Air rune', interval=0.1) #Search for item
    time.sleep(1)
    pyautogui.click(x=select_item_loc[0], y=select_item_loc[1], clicks=1, interval=0, button='left')  #Select item
    time.sleep(1)
    img = np.array(captureScreen(price_per_item_loc))
    price = int(image_to_text(img, True))
    price_ge_format = ge_format(price)
    ge_price = get_price_from_api(data_dict['Air rune'][0]) #Fail safe to check api price incase openCV incorrectly reads the price from image
    if price_ge_format != ge_price and price_ge_format != (str(ge_price)+'.0'):
        print("Error: Price from image is %s but price from ge is %s" % (price_ge_format, ge_price))
        return
    priceIncreasePercentage = int(price * 1.15)
    pyautogui.click(x=change_price_loc[0], y=change_price_loc[1], clicks=1, interval=0, button='left') #Click to change price
    time.sleep(2)
    pyautogui.typewrite(str(priceIncreasePercentage)+'\n', interval=0.1) #type in new price of 75% of original
    time.sleep(1)
    pyautogui.click(x=confirm_loc[0], y=confirm_loc[1], clicks=1, interval=0, button='left') #Click to send buy offer
    time.sleep(1.5)
    #TODO SAVE buy offers to list
    

def sell(slot):
    # time.sleep(2)
    # pyautogui.click(x=collect_item_loc[0], y=collect_item_loc[1], clicks=1, interval=0, button='left') #Click to collect items
    # time.sleep(2)
    # pyautogui.click(x=collect_change_loc[0], y=collect_change_loc[1], clicks=1, interval=0, button='left') #Click to collect change
    # time.sleep(2)
    #Check the history to get bought price
    pyautogui.click(x=history_exchange_button_loc[0], y=history_exchange_button_loc[1], clicks=1, interval=0, button='left') #Click on history button
    time.sleep(2)
    img = np.array(captureScreen(trade_history_item_loc))
    time.sleep(1)
    trade_history_item_str = image_to_text(img, False)
    if not trade_history_item_str:
        print("Unknown trade history item:", trade_history_item_str)
        return
    print(trade_history_item_str)
    img = np.array(captureScreen(trade_history_price_loc))
    time.sleep(1)
    trade_history_price_str = image_to_text(img, True)
    if not trade_history_price_str:
        print("Unknown trade history price:", trade_history_price_str)
        return
    print(trade_history_price_str)
    trade_history_price_str = int(trade_history_price_str)
    pyautogui.click(x=history_exchange_button_loc[0], y=history_exchange_button_loc[1], clicks=1, interval=0, button='left') #Click on exchange button
    time.sleep(2)
    #Begin to make sell transaction TODO

#Sell an item to get the "buy price"
def findMarginSell(slot):
    pyautogui.click(x=history_exchange_button_loc[0], y=history_exchange_button_loc[1], clicks=1, interval=0, button='left') #Click on exchange button
    time.sleep(1.5)
    pyautogui.click(x=slot[0][0]+70, y=slot[0][1]+100, clicks=1, interval=0, button='left') #Click to set up a sell offer
    time.sleep(1.5)
    pyautogui.click(x=inventory_first_slot_loc[0], y=inventory_first_slot_loc[1], clicks=1, interval=0, button='left') #The item to sell should be in the first slot in invent
    time.sleep(1)
    img = np.array(captureScreen(price_per_item_loc))
    price = int(image_to_text(img, True))
    # price_ge_format = ge_format(price)
    # ge_price = get_price_from_api(trade_history_item_str) #Fail safe to check api price incase openCV incorrectly reads the price from image
    # if price_ge_format != ge_price and price_ge_format != (str(ge_price)+'.0'):
    #     print("Error: Price from image is %s but price from ge is %s" % (price_ge_format, ge_price))
    #     return
    priceDecreasePercentage = int(price * 0.85)
    pyautogui.click(x=change_price_loc[0], y=change_price_loc[1], clicks=1, interval=0, button='left') #Click to change price
    time.sleep(2)
    pyautogui.typewrite(str(priceDecreasePercentage)+'\n', interval=0.1) #type in new price of 0.85x of original
    time.sleep(1)
    # pyautogui.click(x=confirm_loc[0], y=confirm_loc[1], clicks=1, interval=0, button='left') #Click to send sell offer
    # time.sleep(1.5)

def isBuyOfferComplete(slot):
    #Check if buy offer finished (green color)
    green = (0, 95, 0) #bgr green
    img = np.array(captureScreen(slot[1]))
    for x in range(0, img.shape[0]):
        for y in range(0, img.shape[1]):
            r, g, b = img[x][y]
            if (r,g,b) == green:
                xPos = slot[1][0]
                yPos = slot[1][1]
                print("Clicking at: ", xPos, yPos)
                pyautogui.click(x=xPos, y=yPos, clicks=1, interval=0, button='left')  #Click completed offered
                return True
    return False

#Setup a buy offer to get the "Sell Price"
def findMarginBuy(slot):
    pyautogui.click(x=slot[0][0]+20, y=slot[0][1]+100, clicks=1, interval=0, button='left') #Click to set up offer
    time.sleep(1)
    db.connect()
    numRows = db.itemSheet.row_count
    row = db.itemSheet.row_values(random.randint(2,numRows)) #Get a random item 
    pyautogui.typewrite("Air rune", interval=0.1) #Search for item
    time.sleep(1)
    pyautogui.click(x=select_item_loc[0], y=select_item_loc[1], clicks=1, interval=0, button='left')  #Select item
    time.sleep(1)
    img = np.array(captureScreen(price_per_item_loc))
    price = int(image_to_text(img, True))
    price_ge_format = ge_format(price)
    ge_price = get_price_from_api(data_dict["Air rune"][0]) #Fail safe to check api price incase openCV incorrectly reads the price from image
    if price_ge_format != ge_price and price_ge_format != (str(ge_price)+'.0'):
        print("Error: Price from image is %s but price from ge is %s" % (price_ge_format, ge_price))
        return
    priceIncreasePercentage = int(price * 1.15)
    pyautogui.click(x=change_price_loc[0], y=change_price_loc[1], clicks=1, interval=0, button='left') #Click to change price
    time.sleep(2)
    pyautogui.typewrite(str(priceIncreasePercentage)+'\n', interval=0.1) #type in new price of 1.15x of original
    time.sleep(1)
    pyautogui.click(x=confirm_loc[0], y=confirm_loc[1], clicks=1, interval=0, button='left') #Click to send buy offer
    time.sleep(1.5)
    data_dict[name][2] = Status.buyingMargin

def collect(slot):
    pyautogui.click(x=slot[0][0]+50, y=slot[0][1]+100, clicks=1, interval=0, button='left') #Click
    time.sleep(1.5)
    pyautogui.click(x=collect_item_loc[0], y=collect_item_loc[1], clicks=1, interval=0, button='left') #Click to collect items
    time.sleep(2)
    pyautogui.click(x=collect_change_loc[0], y=collect_change_loc[1], clicks=1, interval=0, button='left') #Click to collect change
    time.sleep(2) #Check the history to get bought price
    pyautogui.click(x=history_exchange_button_loc[0], y=history_exchange_button_loc[1], clicks=1, interval=0, button='left') #Click on history button
    time.sleep(2)
    img = np.array(captureScreen(trade_history_item_loc))
    time.sleep(1)
    trade_history_item_str = image_to_text(img, False)
    if not trade_history_item_str:
        print("Unknown trade history item:", trade_history_item_str)
        return
    print(trade_history_item_str)
    img = np.array(captureScreen(trade_history_price_loc))
    time.sleep(1)
    trade_history_price_str = image_to_text(img, True)
    if not trade_history_price_str:
        print("Unknown trade history price:", trade_history_price_str)
        return
    print(trade_history_price_str)
    trade_history_price = int(trade_history_price_str) #At this point we have our sell price
    #if data_dict[trade_history_item_str][2] == Status.buyingMargin #TODO LEFT OFF HERE


def main():
    while True:
        for i, slot in enumerate(slots):
            print("Checking status of slot:", (i+1))
            img = np.array(captureScreen(slot[0]))
            imageString = image_to_text(img, False)
            changes = True
            if imageString == 'Empty' and len(margins) < 3:
                print("Finding margin in slot", i)
                findMarginBuy(slot)
                print("Margins:", margins)
                continue
            elif imageString == 'Empty':
                print("Buying in slot", i, "!!!")
                buy(slot)
            elif imageString == 'Buy' and len(margins) < 3:
                complete = isBuyOfferComplete(slot)
                if complete:
                   collect(slot)
            elif imageString == 'Buy':
                complete = isBuyOfferComplete(slot)
                if complete:
                   sell(slot)
            else:
                print("Waiting on new status")
                changes = False

            # if changes:
            #     updatePickleFile() #TODO add a message here and print it out if the pickle file was updated
        print("Sleeping 3")
        time.sleep(3)

#Global variables
print("Starting program...")
setActiveWindow(findGameWindow('RuneLite - Camarine'))
showWindow(findGameWindow('RuneLite - Camarine'))
gsc = getWindowRect(findGameWindow('RuneLite - Camarine')) #Game screen coordinates
cash_stack = 18000000 #18m cash stack to work with
profit = 0
# { 'Air rune': [item_id, buy_limit, status.ENUM, last_price_bought, last_quantity_bought, buy_offer_in_seconds, buy_offer_done_seconds, sell_offer_in_seconds, sell_offer_out_seconds, profit, elapsed_time_hours]
#   'Fire rune': []...
# } ...
print("Loaded pickle")
margins = [] #[[item_name, sell_price, buy_price], [item_name, sell_price, buy_price], [item_name, sell_price, buy_price]]
slots = list()
slots.append([(gsc[0]+80, gsc[1]+215, gsc[2]-620, gsc[3]-527), (gsc[0]+70, gsc[1]+270, gsc[2]-650, gsc[3]-450)]) #The 4 indices are for buy/empty image, next 4 are for buy/sell status
slots.append([(gsc[0]+180, gsc[1]+215, gsc[2]-520, gsc[3]-527), (gsc[0]+180, gsc[1]+270, gsc[2]-520, gsc[3]-450)])
slots.append([(gsc[0]+300, gsc[1]+215, gsc[2]-410, gsc[3]-527), (gsc[0]+300, gsc[1]+270, gsc[2]-310, gsc[3]-450)])

price_per_item_loc = (gsc[0]+340, gsc[1]+308, gsc[2]-330, gsc[3]-438)
change_price_loc = (gsc[0]+425, gsc[1]+370)
select_item_loc = (gsc[0]+80, gsc[1]+680) #location of the first item in the "What would you like to buy?" screen
confirm_loc = (gsc[0]+300, gsc[1]+440)
collect_item_loc = (gsc[0]+450, gsc[1]+450)
collect_change_loc = (gsc[0]+500, gsc[1]+440)
history_exchange_button_loc = (gsc[0]+80, gsc[1]+195)
trade_history_item_loc = (gsc[0]+180, gsc[1]+195, gsc[2]-500, gsc[3]-553)
trade_history_price_loc = (gsc[0]+350, gsc[1]+207, gsc[2]-310, gsc[3]-540)
inventory_first_slot_loc = (gsc[0]+625, gsc[1]+475)

if __name__ == "__main__":
    main()