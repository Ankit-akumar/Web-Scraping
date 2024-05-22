import json
import yaml
import sys
from login import *
import re
from bs4 import BeautifulSoup as bs
from selenium import webdriver


def readDataFromFile():
    with open('backup/depBkp.json','r') as file:
        data = json.load(file)

        if 'subscription_urls' in data:
            subscription_urls = data['subscription_urls']
            print(subscription_urls)

        if 'currentRunningMap' in data:
            currentRunningMap = data['currentRunningMap']
            print(currentRunningMap)
        
        result_dict = {}
        result_dict['currentRunningMap'] = currentRunningMap
        result_dict['subscription_urls'] = subscription_urls
        return result_dict
    
def stopSystem(driver, URL):
    driver.get(URL+'system/')
    try:
        buttons = driver.find_elements(By.CLASS_NAME, "emergency-stop-button")
        for button in buttons:
            if button.text == "STOP SYSTEM":
               # button.click()
               print('found stop system button')
               break
    except Exception as e:
        print(e)
        

def uploadMap(URL, mdDriver, currentRunningMap):
    driver = mdDriver
    driver.get(URL)
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
            driver.get(URL+'view/'+mapId)
            time.sleep(5)
            driver.find_element(By.CLASS_NAME, 'upload-map').click()
            time.sleep(1)
            input_element_bfs = driver.find_element(By.XPATH, "//input[@class='form-control' and @placeholder='bfs']")
            input_element_port = driver.find_element(By.XPATH, "//input[@class='form-control' and @placeholder='4000']")
            if input_element_bfs and input_element_port:

                # SMS should be checked, IMS unchecked and Sister unchecked
                input_element_sms = driver.find_element(By.XPATH, "//input[@class='form-check-input' and @value='sms']")
                if input_element_sms:
                    input_element_sms_is_checked = input_element_sms.get_attribute("checked")
                    if input_element_sms_is_checked is None:
                        input_element_sms.click()
                    
                    input_element_ims = driver.find_element(By.XPATH, "//input[@class='form-check-input' and @value='ims-backend']")
                    if input_element_ims:
                        input_element_ims_is_checked = input_element_ims.get_attribute('checked')
                        if input_element_ims_is_checked:
                            input_element_ims.click()
                    else:
                        print('IMS not found')

                    input_element_sister = driver.find_element(By.XPATH, "//input[@class='form-check-input' and @value='induct-manager']")
                    if input_element_sister:
                        input_element_sister_is_checked = input_element_sister.get_attribute('checked')
                        if input_element_sister_is_checked:
                            input_element_sister.click()
                    
                        time.sleep(2)
                        upload_btn = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-success")
                        if upload_btn:
                            print('found')
                        time.sleep(10)
                    else:
                        print('Sister not found')
                else:
                     print('SMS not found')
            else:
                print('bfs and port not found')


def updateSubscriptionUrls(sorterDriver, subscription_urls, URL):
    driver = sorterDriver
    driver.get(URL)

    pageSource = driver.page_source
    soup = bs(pageSource, 'html.parser')
    eventList = soup.find_all('th', class_='field-pk')

    keysList = []
    for event in eventList:
        keysList.append(subscription_urls[event.get_text()])
    
    i = 1
    for key in keysList:
        x_path = "(//input[@class='vTextField'])["+str(i)+"]"
        input_element = driver.find_element(By.XPATH, x_path)
        input_element.clear()
        input_element.send_keys(key)
        i+=1

    time.sleep(2)

    submit_btn = driver.find_element(By.XPATH, "(//input[@type='submit'])")
    if submit_btn:
        print('found')
        print(submit_btn.get_attribute('name'))
    driver.quit()


login = Login()

driver = webdriver.Chrome()

try:
    with open('auth.yml', 'r') as file:
        conf = yaml.load(file, Loader=yaml.SafeLoader)
    URL = conf['user']['url']
    username = conf['user']['username']
    password = conf['user']['password']
except Exception as e:
    print("Error occured while accessing auth.yml file: '{e}'")
    sys.exit(1)

result_dict = readDataFromFile()

sorterDbDriver = login.login(URL+"sorter/login/", "id_username", "id_password", "submit-row", username, password)

updateSubscriptionUrls(sorterDbDriver, result_dict['subscription_urls'], URL+'sorter/data/subscription/')

driver = login.loginMD(URL+"login/", username, password)
stopSystem(driver, URL)

uploadMap(URL+'map-creator/', driver, result_dict['currentRunningMap'])
