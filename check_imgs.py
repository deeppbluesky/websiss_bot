
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from datetime import datetime
import configparser
import logging
import getopt
import time
import sys
import csv
import json
import shutil
import string
import random
import os
from PIL import Image
import numpy as np
import cv2
import pytesseract
import pyautogui
import requests

# import pyocr
# import pyocr.builders

WAIT_TIMEOUT = 7

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

# Configure browser session
wd_options = Options()
wd_options.add_argument("--disable-notifications")
wd_options.add_argument("--disable-infobars")
wd_options.add_argument("--start-maximized")
wd_options.add_argument("--mute-audio")
wd_options.add_experimental_option("prefs", {
  "download.default_directory": str(os.path.dirname(os.path.abspath(__file__))) + "\\images",
  "download.prompt_for_download": True,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

# browser = webdriver.Chrome(chrome_options=wd_options)

def get_by_xpath(driver, xpath):
    """
    Get a web element through the xpath passed by performing a Wait on it.
    :param driver: Selenium web driver to use.
    :param xpath: xpath to use.
    :return: The web element
    """
    return WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located(
            (By.XPATH, xpath)
        ))


def get_by_class_name(driver, class_name):
    """
    Get a web element through the class_name passed by performing a Wait on it.
    :param driver: Selenium web driver to use.
    :param class_name: class_name to use.
    :return: The web element
    """
    return WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located(
            (By.CLASS_NAME, class_name)
        ))

# --------------- Write all fails into CSV format ---------------
def write_fails(fails, now):
    # Prep CSV Output File
    csvOut = 'fails_%s.csv' % now.strftime("%Y-%m-%d")
    writer = csv.writer(open(csvOut, 'w+', encoding="utf-8"))
    writer.writerow(['image', 'tesseract', 'tries'])

    # Write friends to CSV File
    for fail in fails:
        writer.writerow([fail['image'], fail['tesseract'], fail['tries']])

    print("Successfully saved to %s" % csvOut)

# --------------- Write all ckecks into CSV format ---------------
def write_check(check_list, now):
    # Prep CSV Output File
    csvOut = 'check_list_%s.csv' % now.strftime("%Y-%m-%d_%H%M")
    writer = csv.writer(open(csvOut, 'w+', encoding="utf-8"))
    writer.writerow(['correct', 'tesseract', 'tries'])

    # Write friends to CSV File
    for check in check_list:
        writer.writerow([check['correct'], check['tesseract'], check['tries']])

    print("Successfully saved to %s" % csvOut)

def convert_bgr_color(img):
    bgr = [214, 134, 35]
    thresh = 50
    imgYCB = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    cv2.imwrite("IMG_YCB.png", imgYCB)
    # cv2.imshow("Result IMG_YCB", imgYCB)
    imgBGR = convert_3d(imgYCB, bgr, thresh)
    img = cv2.imread("IMG_BGR.png")
    # cv2.imshow("Result IMG_BGR", imgBGR)
    return imgBGR

def convert_3d(img, color_array, thresh):
    #convert 1D array to 3D, then convert it to YCrCb and take the first element
    minSC = np.array([color_array[0] - thresh, color_array[1] - thresh, color_array[2] - thresh])
    maxSC = np.array([color_array[0] + thresh, color_array[1] + thresh, color_array[2] + thresh])

    maskSC = cv2.inRange(img, minSC, maxSC)
    resultSC = cv2.bitwise_and(img, img, mask=maskSC)
    cv2.imwrite("IMG_YCB2.png", resultSC)
    return resultSC

def rezize_img(img):
    img_resize = cv2.resize(img,(102,48))
    cv2.imwrite("1/img_resize.png",img_resize)
    return img_resize

def convert_binary(img):
    print(img.shape)
    img_bin = cv2.inRange(img, (198, 121, 1), (233, 160, 75))
    # cv2.imshow('threshoalded',img_bin)
    cv2.imwrite("IMG_BIN_.png",img_bin)
    return img_bin


def clean_img(img):
    cv2.rectangle(img, (0, 20), (73, 25), (0, 0, 0), cv2.FILLED)
    cv2.imwrite("IMG_BLACK_LINE.png", img)
    # cv2.imshow('rectangle', img)
    img_bin = cv2.bitwise_not(img)
    cv2.imwrite("IMG_BIN.png", img)
    return img_bin

def crop_img(img):
    crop_img = img[0:21, 0:81]
    cv2.imwrite("croped.png",crop_img)
    return crop_img

def img_process(img_path):
    img = cv2.imread(img_path)
    # cv2.imshow("Imagen Original", img)
    imgCroped = crop_img(img)
    # print imgCroped.shape
    # cv2.imshow("Result Croped", imgCroped)
    
    imgBGR = convert_bgr_color(imgCroped)
    cv2.imwrite("IMG_BGR.png", imgBGR)
    imgBin = convert_binary(imgBGR)
    img = cv2.imread("IMG_BIN_.png")
    imgBin = clean_img(imgBin)
    img_resized = rezize_img(imgBin)
    # img_path = "1/img_resize.png"	
    return imgBin

def get_text(img_path):
    # tessdata_dir_config = r'--psm 6 bazaar'
    # tessdata_dir_config = r'--psm 6 bazaar'
    tessdata_dir_config = r'--psm 8 --user-patterns eng.user-patterns'
    code = pytesseract.image_to_string(Image.open(
        img_path), lang='eng', config=tessdata_dir_config)
    code = code.replace(" ", "")
    print(code)
    return code

# def get_text2(img_path):
#     tools = pyocr.get_available_tools()[0]
#     code = tools.image_to_string(Image.open(img_path), builder=pyocr.builders.DigitBuilder())
#     # code = pytesseract.image_to_string(Imagenage.open(
#     #     img_path), lang='eng', config=tessdata_dir_config)
#     # code = code.replace(" ", "")
#     print(code)
#     return code


def numbers_to_strings(argument):
    switcher = {
        1: lambda : "uno",
        2: lambda : "dos",
        3: lambda : "tres",
        4: lambda : "cuatro",
        5: lambda : "cinco"
    }
    # Get the function from switcher dictionary
    func = switcher.get(argument, "nothing")
    # Execute the function
    return func()

# Log in and navigate to group's page
def ws_login(credentials, img_path, fails, check_list, tries, now):
    # tries +=1
    
    # shutil.copyfile('C:\\Users\\Mauricio\\Downloads\\captcha.png', 'C:\\Users\\Mauricio\\Desktop\\websiss_bot\\images\\captcha.png')

    # img = img_process("bins/"+img_path)
    code = get_text("bins/"+img_path)
    name = ''.join(random.sample(string.ascii_lowercase, 7))
    # shutil.copyfile('./1/img_resize.png',
                        # r"./fails/captcha-{}.png".format(tries))

    name = img_path.split('.')[0]

    print("              ", img_path, " <=> ", code)
    if(code in img_path):
    		logger.info("CHECK OK!!!")
    		tries = "OK"
    else:
  			logger.info("CHECK FAIL!!!")
  			tries = "FAIL"

    check_list.append({
    		'correct': name,
        'tesseract': code,
        'tries': tries
        })
    write_check(check_list, now)
      

def main(argv):
    filePath = ''
    configPath = ''
    limit = ''
    fails = []
    corrects = []
    tries = 0
    now = datetime.now()
    opts, args = getopt.getopt(argv, "l:c:")
    if opts:
        for o, a in opts:
            if o == "-l":
                limit = a
            if o == "-c":
                configPath = a
    if configPath:
        configObj = configparser.ConfigParser()
        configObj.read(configPath)
        # email = configObj.get('credentials', 'email')
        # password = configObj.get('credentials', 'password')
        # id_group = configObj.get('group', 'id')
        
        listdir = os.listdir("bins")

        for img_name in listdir:
        	ws_login(configObj, img_name, fails, corrects, tries, now)
        	tries+=1
        # ws_login(configObj, "QIB8718.png", fails, corrects, tries, now)

    else:
        print('USAGE: ')
        print('python websiss.py -c config.txt')

if __name__ == '__main__':
    main(sys.argv[1:])



