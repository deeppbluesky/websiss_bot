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
import base64
import os
from PIL import Image
import numpy as np
import cv2
import pytesseract
import pyautogui
import requests

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

browser = webdriver.Chrome(chrome_options=wd_options)


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


def get_by_name(driver, name):
    """
    Get a web element through the class_name passed by performing a Wait on it.
    :param driver: Selenium web driver to use.
    :param class_name: class_name to use.
    :return: The web element
    """
    return WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located(
            (By.NAME, name)
        ))


def get_by_tag_name(driver, tag_name):
    """
    Get a web element through the class_name passed by performing a Wait on it.
    :param driver: Selenium web driver to use.
    :param class_name: class_name to use.
    :return: The web element
    """
    return WebDriverWait(driver, WAIT_TIMEOUT).until(
        ec.presence_of_element_located(
            (By.TAG_NAME, tag_name)
        ))

    def get_by_id(driver, id_name):
        """
        Get a web element through the class_name passed by performing a Wait on it.
        :param driver: Selenium web driver to use.
        :param class_name: class_name to use.
        :return: The web element
        """
        return WebDriverWait(driver, WAIT_TIMEOUT).until(
            ec.presence_of_element_located(
                (By.ID, id_name)
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

# --------------- Write all corrects into CSV format ---------------
def write_corrects(corrects, now):
    # Prep CSV Output File
    csvOut = 'corrects_%s.csv' % now.strftime("%Y-%m-%d")
    writer = csv.writer(open(csvOut, 'w+', encoding="utf-8"))
    writer.writerow(['tesseract', 'tries'])

    # Write friends to CSV File
    for correct in corrects:
        writer.writerow([correct['tesseract'], correct['tries']])

    print("Successfully saved to %s" % csvOut)

def get_captcha(driver, img, captcha_number):
    img_captcha_base64 = driver.execute_async_script(
        """
        var ele = arguments[0], callback = arguments[1];
        ele.addEventListener('load', function fn(){
        ele.removeEventListener('load', fn, false);
        var cnv = document.createElement('canvas');
        cnv.width = this.width; cnv.height = this.height;
        cnv.getContext('2d').drawImage(this, 0, 0);
        callback(cnv.toDataURL('image/png').substring(22));
        }, false); ele.dispatchEvent(new Event('load'));
        """, img
    )
    # with open(r"./captchas/captcha-{}.png".format(captcha_number), 'wb') as f:
    with open(r"./images/captcha.png", 'wb') as f:
        f.write(base64.b64decode(img_captcha_base64))

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
    # convert 1D array to 3D, then convert it to YCrCb and take the first
    # element
    minSC = np.array(
        [color_array[0] - thresh, color_array[1] - thresh, color_array[2] - thresh])
    maxSC = np.array(
        [color_array[0] + thresh, color_array[1] + thresh, color_array[2] + thresh])

    maskSC = cv2.inRange(img, minSC, maxSC)
    resultSC = cv2.bitwise_and(img, img, mask=maskSC)
    cv2.imwrite("IMG_YCB2.png", resultSC)
    return resultSC


def rezize_img(img):
    img_resize = cv2.resize(img, (98, 46))
    cv2.imwrite("1/img_resize.png", img_resize)
    return img_resize


def convert_binary(img):
    print(img.shape)
    img_bin = cv2.inRange(img, (198, 121, 1), (233, 160, 75))
    # cv2.imshow('threshoalded', img_bin)
    cv2.imwrite("IMG_BIN_.png", img_bin)
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
    cv2.imwrite("croped.png", crop_img)
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
    tessdata_dir_config = r'-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ -l eng --psm 6'
    code = pytesseract.image_to_string(Image.open(
        img_path), lang='eng', config=tessdata_dir_config)
    code = code.replace(" ", "")
    print(code)
    return code


def numbers_to_strings(argument):
    switcher = {
        1: lambda: "uno",
        2: lambda: "dos",
        3: lambda: "tres",
        4: lambda: "cuatro",
        5: lambda: "cinco"
    }
    # Get the function from switcher dictionary
    func = switcher.get(argument, "nothing")
    # Execute the function
    return func()

# Log in and navigate to group's page


def ws_login(credentials, img_path, fails, corrects, tries, now):
    tries += 1
    # browser.get('http://websis.umss.edu.bo/stud_codVerificacion.asp')
    # pyautogui.hotkey('ctrl', 's')
    # time.sleep(2)
    # pyautogui.typewrite("captcha.png")
    # time.sleep(1)
    # pyautogui.hotkey('enter')
    # # time.sleep(1)
    # pyautogui.hotkey('alt', 'y')
    # # time.sleep(1)
    # pyautogui.hotkey('enter')
    # time.sleep(2)
    # shutil.copyfile('C:\\Users\\Mauricio\\Downloads\\captcha.png',
    #                 'C:\\Users\\Mauricio\\Desktop\\websiss_bot\\images\\captcha.png')

    browser.get('http://websis.umss.edu.bo/serv_estudiantes.asp')

    img = get_by_xpath(browser, "//*[@id='idFrmLogin']/table/tbody/tr[6]/td/img")
    captcha_number = 0
    get_captcha(browser, img, captcha_number)

    codigosis = credentials.get('credentials', 'codigosis')
    password = credentials.get('credentials', 'password')
    dia = credentials.get('fechanac', 'dia')
    mes = credentials.get('fechanac', 'mes')
    anio = credentials.get('fechanac', 'anio')

    logger.info('Log in - Searching for the codsis input')
    browser.find_element_by_id('idCuenta').send_keys(codigosis)

    logger.info('Log in - Searching for the password input')
    browser.find_element_by_id('idContrasena').send_keys(password)

    logger.info('Log in - Searching for the month option')
    s1 = Select(browser.find_element_by_id('idFND'))
    e1 = browser.find_element_by_id('idFND')
    s1.select_by_value(dia)
    browser.execute_script(
        "arguments[0].setAttribute('style', 'visibility:hidden')", e1)

    logger.info('Log in - Searching for the year option')
    s2 = Select(browser.find_element_by_id('idFNM'))
    e2 = browser.find_element_by_id('idFNM')
    s2.select_by_value(mes)
    browser.execute_script(
        "arguments[0].setAttribute('style', 'visibility:hidden')", e2)

    logger.info('Log in - Searching for day option')
    s3 = Select(browser.find_element_by_id('idFNA'))
    e3 = browser.find_element_by_id('idFNA')
    s3.select_by_value(anio)
    browser.execute_script(
        "arguments[0].setAttribute('style', 'visibility:hidden')", e3)

    # a = input("Please enter the code captcha and press enter after the page loads...")
    img = img_process(img_path)
    code = get_text("1/img_resize.png")

    logger.info('Sending the code captcha')
    browser.find_element_by_id('idCodigo').send_keys(code)

    logger.info('Log in - Searching for the submit button')
    browser.find_element_by_id('idBtnSubmit').click()

    # time.sleep(7)
    is_logged = -1
    try:
        print(browser.current_url)
        img_success = get_by_xpath(
            browser, "/html/body/table[6]/tbody/tr/td[2]/table[1]/tbody/tr/td[3]/img")
        print(img_success)
        txt_gral_info = get_by_xpath(
            browser, "/html/body/table[6]/tbody/tr/td[1]/table/tbody/tr[1]/td").text
        print(txt_gral_info)

        print(browser.current_url)
        main_url = "http://websis.umss.edu.bo/stud_main.asp"
        if("Información General" in txt_gral_info):
            logger.info("captcha correcto!!!")
            is_logged = 2
            corrects.append({
                'tesseract': code,
                'tries': tries
            })
            write_corrects(corrects, now)
            shutil.copyfile('C:\\Users\\Mauricio\\Desktop\\websiss_bot\\images\\captcha.png',
                            'C:\\Users\\Mauricio\\Desktop\\websiss_bot\\corrects\\%s.png' % code)
        else:
            pass

    except:
        logger.info("Error: No se pudo encontrar el elemento mensaje de alerta")
        logger.info("captcha incorrecto")
        name = ''.join(random.sample(string.ascii_lowercase, 7))
        logger.info(name)
        # ws_login(credentials, img_path, fails, corrects, tries, now)
        fails.append({
            'image': name,
            'tesseract': code,
            'tries': tries
        })
        write_fails(fails, now)
        shutil.copyfile("C:\\Users\\Mauricio\\Desktop\\websiss_bot\\images\\captcha.png",
                        "C:\\Users\\Mauricio\\Desktop\\websiss_bot\\fails\\%s.png" % name)

    if(is_logged == 2):
        logger.info("Going to inscription...")
        browser.get(
            'http://websis.umss.edu.bo/stud_loginInscripcion.asp?codser=STUD&idcat=39')

        cod1 = get_by_xpath(
            browser, "//*[@id='idFrmLogin']/table/tbody/tr[1]/td[1]/span").text
        cod2 = get_by_xpath(
            browser, "//*[@id='idFrmLogin']/table/tbody/tr[2]/td[1]/span").text
        cod1 = int(''.join(list(filter(str.isdigit, cod1))))
        cod2 = int(''.join(list(filter(str.isdigit, cod2))))

        cod1 = numbers_to_strings(cod1)
        cod2 = numbers_to_strings(cod2)

        cod1 = credentials.get('matricula', cod1)
        cod2 = credentials.get('matricula', cod2)

        logger.info('Sending the access code')
        browser.find_element_by_id('idInput1').send_keys(cod1)
        browser.find_element_by_id('idInput2').send_keys(cod2)

        logger.info('Clicking on submit button')
        browser.find_element_by_id('idBtnSubmit').click()

        time.sleep(3)
        # logger.info('Ok')
        msg = get_by_xpath(
            browser, "/html/body/table[6]/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td").text

        txt_alert_msg = get_by_xpath(
            browser, "/html/body/table[6]/tbody/tr/td[1]/table/tbody/tr[1]/td").text
        main_url = "http://websis.umss.edu.bo/stud_main.asp"
        msg1 = "El ciclo de inscripción principal esta cerrado"
        msg2 = "La carrera en la que desea inscribirse no esta inscribiendo en este momento"
        if((msg1 in txt_alert_msg) or (msg2 in txt_alert_msg)):
            # is_logged = 2
            logger.info(msg)
        else:
            is_logged = 1

    return is_logged


def enroll(credentials, cod_materia, docente):
    logger.info("Going to inscription...")
    browser.get(
        'http://websis.umss.edu.bo/stud_inscripcion.asp?codSer=STUD&idCat=39')

    try:
        alert = browser.switch_to_alert()
        alert.accept()
        print("################################ Alert accepted")
    except:
        print("################################ No alert")

    time.sleep(3)
    # logger.info('Ok')
    msg = get_by_xpath(
        browser, "/html/body/table[6]/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td").text
    logger.info(msg)

    logger.info('Enroll - subject')
    browser.find_element_by_id('idBtnAnadir').click()

    try:
        alert = browser.switch_to_alert()
        alert.accept()
        print("################################ Alert accepted")
    except:
        print("################################ No alert")

    materia_row = "//table[6]//td[contains(text(), '" + cod_materia + "')]/.."
    docente_option = "//select[@name='grupo']/option[contains(text(),'" + \
        docente + "')]"

    parent_row = get_by_xpath(browser, materia_row)
    # get the parent of td element
    enroll_btn = get_by_xpath(
        parent_row, ".//button[contains(text(), 'Inscribirse')]")
    logger.info('Clicking on Enroll button')
    enroll_btn.click()

    try:
        alert = browser.switch_to_alert()
        alert.accept()
        print("################################ Alert accepted")
    except:
        print("################################ No alert")

    try:
        # logger.info('Choicing - Docente')
        # s1 = Select(get_by_name(browser, 'grupo'))
        option = get_by_xpath(browser, docente_option)
    except:
        logger.info('No cargo la pagina de grupos')

    # get_by_xpath(s1, "//select/option[contains(text(), 'ARISPE')]")
    # s1.select_by_value()
    is_enrolled = False
    current_url = "stud_inscripcion.asp"
    if(option):
        try:

            # s1 = Select(browser.find_element_by_name('grupo'))
            # get_by_xpath(s1, "//select/option[contains(text(), 'ARISPE')]")

            print('#########################  Hay el %s!!!  #########################'
                  % docente)
            enroll_btn = get_by_xpath(browser,
                                      "//button[contains(text(), 'Inscribirse a la materia')]"
                                      )
            enroll_btn.click()
            time.sleep(2)

            # if(current_url not in browser.current_url):

            try:
                alert = browser.switch_to_alert()
                alert.accept()
                print('################################ Alert accepted')
            except:
                print('################################ No alert')
                print(browser.current_url)
            try:
                materia_row = "//table[6]//td[contains(text(), '" \
                    + cod_materia + "')]"
                is_present = get_by_xpath(browser, materia_row)
                if is_present:
                    print('INSCRITO!!!')
                    is_enrolled = True
            except:
                print('No se pudo inscribir')
        except:
            print('######################### No hay el %s!!!' % docente)

    return is_enrolled


def change_subject(credentials, cod_materia, docente):
    browser.get(
        'http://websis.umss.edu.bo/stud_inscripcion.asp?codSer=STUD&idCat=39')

    # get the parent of td element
    # status_btn = get_by_id(browser, "idBtnInscripcion")
    # logger.info('Clicking on Estado de Inscripcion button')
    # status_btn.click()

    try:
        alert = browser.switch_to_alert()
        alert.accept()
        print("################################ Alert accepted")
    except:
        print("################################ No alert")

    time.sleep(3)
    # logger.info('Ok')
    msg = get_by_xpath(
        browser, "/html/body/table[6]/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td").text
    logger.info(msg)

    # logger.info('Enroll - subject')
    # browser.find_element_by_id('idBtnAnadir').click()

    try:
        alert = browser.switch_to_alert()
        alert.accept()
        print("################################ Alert accepted")
    except:
        print("################################ No alert")

    # try:
        #  status_btn = get_by_id(browser, "idBtnInscripcion")
        #  logger.info('Clicking on Estado de Inscripcion button')
        #  status_btn.click()
    # except:
    # 	pass

    materia_row = "//table[6]//td[contains(text(), '" + cod_materia + "')]/.."
    docente_option = "//select[@name='grupo']/option[contains(text(),'" + \
        docente + "')]"

    parent_row = get_by_xpath(browser, materia_row)
    # get the parent of td element
    enroll_btn = get_by_xpath(
        parent_row, ".//button[contains(text(), 'Cambiar')]")
    logger.info('Clicking on Enroll button')
    enroll_btn.click()

    try:
        alert = browser.switch_to_alert()
        alert.accept()
        print("################################ Alert accepted")
    except:
        print("################################ No alert")

    try:
        # logger.info('Choicing - Docente')
        # s1 = Select(get_by_name(browser, 'grupo'))
        option = get_by_xpath(browser, docente_option)
    except:
        logger.info('No cargo la pagina de grupos')

    # get_by_xpath(s1, "//select/option[contains(text(), 'ARISPE')]")
    # s1.select_by_value()
    is_changed = False
    current_url = "stud_inscripcion.asp"
    time.sleep(2)
    if(option):
        try:

            # s1 = Select(browser.find_element_by_name('grupo'))
            # get_by_xpath(s1, "//select/option[contains(text(), 'ARISPE')]")
            option.click()
            print('#########################  Hay el %s!!!  #########################'
                  % docente)
            enroll_btn = get_by_xpath(browser,
                                      "//button[contains(text(), 'Cambiar de Grupo')]"
                                      )
            enroll_btn.click()
            time.sleep(2)

            # if(current_url not in browser.current_url):

            try:
                alert = browser.switch_to_alert()
                alert.accept()
                print('################################ Alert accepted')
            except:
                print('################################ No alert')
                print(browser.current_url)
            try:
                materia_row = "//table[6]//td[contains(text(), '" \
                    + cod_materia + "')]"
                is_present = get_by_xpath(browser, materia_row)
                if(is_present):
                    print('INSCRITO!!!')
                    is_changed = True
            except:
                print('No se pudo cambiar')
        except:
            print('######################### No hay el %s!!!' % docente)
    return is_changed


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
        # emaiql = configObj.get('credentials', 'email')
        # password = configObj.get('credentials', 'password')
        # id_group = configObj.get('group', 'id')
        logged = False
        i = 1
        while (i <= 4 and not logged):
            i += 1
            logged = ws_login(configObj, "images/captcha.png",
                              fails, corrects, tries, now)
            if(logged == 1):
                is_changed = False
                logged = True
                # is_changed = True
                while(not is_changed):
                    is_changed = enroll(configObj, '2014087', 'ARISPE')
            elif(logged == 2):
                print("El ciclo de inscripción principal esta cerrado")
                break
            elif(logged == -1):
                logged = False

    else:
        print('USAGE: ')
        print('python websiss.py -c config.txt')

if __name__ == '__main__':
    main(sys.argv[1:])
