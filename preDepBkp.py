from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from login import Login
import re
import yaml
import time
import json
import logging
import datetime
import os
import sys

def checkFiles():
    if not os.path.exists('auth.yml'):
        print('ERROR: auth.yml file is not present in this directory.')
    if not os.path.exists('backup/depBkp.json'):
        print('ERROR: depBkp.json file is not present in this directory')
        

def createLogFile():
    logs_directory = 'logs'

    # Creating the logs directory to store logs if not already present
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
        print(f"'{logs_directory}' Directory created.")
        
    currentDateTime = datetime.datetime.now()
    formatedDateTime = currentDateTime.strftime("%Y-%m-%d_%H-%M-%S")
    fileName = f"log_{formatedDateTime}.log"
    try:
        filePath = os.path.join(logs_directory,fileName)
        with open(filePath, 'w'):
            print(f"Log file '{fileName}' created.")
            return filePath
    except Exception as e:
        print("An error occured while creating the log file: '{e}' ")
        sys.exit(1)


def setupLogging(filePath):
    logging.basicConfig(filename=filePath, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def writeToFile(filePath, key, value):
    with open(filePath, 'r') as bkpFile:
        contents = json.load(bkpFile)
    contents[key] = value
    with open(filePath, 'w') as bkpFile:
        json.dump(contents, bkpFile, indent=4)


def getSubscriptionUrls(url, sorterDbDriver):
    driver = sorterDbDriver
    driver.get(url)

    try:
        WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "paginator"))
        )
    except Exception as e:
        print("While waiting for the page to load encountered this error:", e)
    finally:
        pageSource = driver.page_source
        soup = bs(pageSource, 'html.parser')

        #getting subscriptions from page source
        eventList = soup.find_all('th', class_='field-pk')
        subscriptionList = soup.find_all('input', class_='vURLField')
        subscriptionsCount = soup.find('p', class_='paginator').get_text(strip=True)
        subscriptionsCount = int(subscriptionsCount[0])
        print(subscriptionsCount)

        fieldIds = []
        subscriptions = []

        for event in eventList:
            fieldIds.append(event.get_text())

        for element in subscriptionList:
            if element and 'value' in element.attrs:
                subscriptions.append(element['value'])
            else:
                print("ERROR: No element and value")

        if (subscriptionsCount == len(fieldIds) and subscriptionsCount == len(subscriptions)):
            print(fieldIds)
            print(subscriptions) 
            return dict(zip(fieldIds,subscriptions))
        else:
            print("ERROR: All the subscription urls were not copied.")


def downloadSorterDevicesConfig(url, sorterDbDriver):
    driver = sorterDbDriver
    driver.get(url)
    time.sleep(3)
    try:
        WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.XPATH, "//td[@class='field-download_devices']"))
        )
    except Exception as e:
        print("While waiting for the page to load encountered this error:", e)
    finally:
        download = driver.find_element(By.XPATH, "//td[@class='field-download_devices']")
        if download:
            anchor = download.find_element(By.TAG_NAME, 'a')
            if anchor:
                anchor.click()
        time.sleep(8)


def downloadSamDevicesConfig(url, samDbDriver):
    driver = samDbDriver
    driver.get(url)
    time.sleep(3)
    try:
        WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.XPATH, "//td[@class='field-download_devices']"))
        )
    except Exception as e:
        print("While waiting for the page to load encountered this error:", e)
    finally:
        download = driver.find_element(By.CLASS_NAME, "field-download_devices")
        if download:
            anchor = download.find_element(By.TAG_NAME, 'a')
            if anchor:
                anchor.click()
        time.sleep(8)


def downloadMDConfig(url, mdDbDriver):
    driver = mdDbDriver
    driver.get(url)
    time.sleep(5)

    # Keep clicking load more btn till all the configs are loaded
    loadMoreBtnPresent = True
    loadMoreBtn = None
    while loadMoreBtnPresent:
        try:
            loadMoreBtn = driver.find_element(By.CLASS_NAME, 'more-btn')
        except:
            print('No load more btn was found')
        finally:
            if loadMoreBtn:
                print('Load more btn found')
                loadMoreBtn.click()
                loadMoreBtn = None
                time.sleep(2)
            else:
                loadMoreBtnPresent = False

    # Downloading the config
    time.sleep(3)
    pageSource = driver.page_source
    soup = bs(pageSource, 'html.parser')
    disabled_input = soup.find('input', {'disabled':True})
    if disabled_input:
        next_anchor_tag = disabled_input.find_next('a')
        if next_anchor_tag:
            href = next_anchor_tag.get('href')
            xpath = f"//a[@href='{href}']"
            driver.find_element(By.XPATH, xpath).click()
            time.sleep(8)
        else:
            print("No anchor tag found after disabled input.")
    else:
        print("No disabled input tag found.")


def getMap(url, mdDbDriver):
    driver = mdDbDriver
    driver.get(url)

    try:
        WebDriverWait(driver,30).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'iframe'))
        )
    except Exception as e:
        print("While waiting for the page to load encountered this error:", e)
    finally:
        frameElement = driver.find_element(By.CLASS_NAME, 'iframe')
        driver.switch_to.frame(frameElement)
        driver.find_element(By.ID, 'openNav').click()
        WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.ID, 'info_side_panel'))
        )
        pageSource = driver.page_source
        soup = bs(pageSource, 'html.parser')
        info_side_panel_div = soup.find('div', id='info_side_panel')
        if info_side_panel_div:
            next_span_tag = info_side_panel_div.find_next('span')
            if next_span_tag:
                span_text = next_span_tag.text.strip()
                driver.find_element(By.CSS_SELECTOR, 'button.btn.close-btn').click()
                time.sleep(2)
                driver.save_screenshot('backup/map.png')
                return span_text
            else:
                print("Span tag not found after div with id 'info_side_panel'")
        else:
            print("Div with id 'info_side_panel' not found")


def downloadMap(url, mdDbDriver, currentRunningMap):
    driver = mdDbDriver
    driver.get(url)
    time.sleep(5)
    driver.find_element(By.CLASS_NAME, 'search-map.form-control').send_keys(currentRunningMap)
    time.sleep(1)
    pattern = re.compile(r'\b' + re.escape(currentRunningMap) + r'\b')
    pageSource = driver.page_source
    soup = bs(pageSource, 'html.parser')
    currentRunningMapText = soup.find('td', string=pattern)
    if currentRunningMapText:
        mapId = currentRunningMapText.find_previous_sibling('td').text.strip()
        print("Map ID copied from Map-creator - "+mapId)
        if mapId:
            driver.get(url+'view/'+mapId)
            time.sleep(5)
            driver.find_element(By.CLASS_NAME, 'download-map').click()
            time.sleep(8)


def downloadSmsConfig(smsDbDriver):
    driver = smsDbDriver
    driver.find_element(By.XPATH, "//a[@href='/sms/admin/info/http_notifiers']").click()
    time.sleep(3)
    divElement = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div[style='float: left;margin-top: 21px;']"))
    )
    divText = divElement.text
    # ofIndex = 


    # pageSource = driver.page_source
    # soup = bs(pageSource, 'html.parser')
    # with open('pgsource.txt','w') as file:
    #     file.write(str(soup))

    # driver.find_element(By.XPATH, "//a[@href='/sms/admin/info/http_notifiers']").click()
    # time.sleep(10)
    # anchor = driver.find_element(By.XPATH, "//a[contains(@class, 'info-btn-RtrHSxT2f9')]")
    # if anchor:
    #     print('found achor')
    #     anchor.click()
    # time.sleep(5)


# # Checking if required files are present
# checkFiles()

# # Creating a log file for this execution
# filePath = createLogFile()

# # set up log file for logging 
# setupLogging(filePath)

# Creating object of login class
login = Login()

try:
    with open('auth.yml', 'r') as file:
        conf = yaml.load(file, Loader=yaml.SafeLoader)
    URL = conf['user']['url']
    username = conf['user']['username']
    password = conf['user']['password']
except Exception as e:
    print("Error occured while accessing auth.yml file: '{e}'")
    sys.exit(1)

# Logging into sorter dashboard and getting driver object 
sorterDbDriver = login.login(URL+"sorter/login/", "id_username", "id_password", "submit-row", username, password)

# getting subscription urls from the sorter dashboard
subscriptionDict = getSubscriptionUrls(URL+"sorter/data/subscription/", sorterDbDriver)

# Writing subscription urls into backup file
writeToFile('backup/depBkp.json', 'subscription_urls', subscriptionDict)

# downloading sorter devices config
downloadSorterDevicesConfig(URL+"sorter/data/installation/", sorterDbDriver)
sorterDbDriver.quit()

# Logging into sam dashboard and getting driver object
samDbDriver = login.login(URL+"sam/login/", "id_username", "id_password", "submit-row", username, password)

# downloading sam devices config
downloadSamDevicesConfig(URL+"sam/gorsam/system/", samDbDriver)
samDbDriver.quit()

# logging into MD and getting driver object
mdDbDriver = login.loginMD(URL+"login/", username, password)

# downloading MD config
downloadMDConfig(URL+"configuration/", mdDbDriver)

# getting the current running map from MD and taking a screenshot of map
currentRunningMap = getMap(URL+"maps/", mdDbDriver)
print("Map name copied from MD - "+currentRunningMap)
writeToFile('backup/depBkp.json','currentRunningMap',currentRunningMap)

# downloading map from map-creator
downloadMap(URL+"map-creator/", mdDbDriver, currentRunningMap)
mdDbDriver.quit()

# logging into SMS and getting driver object
smsDbDriver = login.login(URL+'sms/admin/login/', 'username', 'password', 'btn.btn-primary', username, password)

# downloading sms config (httpnotifiers.csv)
downloadSmsConfig(smsDbDriver)
smsDbDriver.quit()
