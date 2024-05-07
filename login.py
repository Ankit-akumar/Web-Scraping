from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# Login into dashboards
class Login:
    # General login method
    def login(self, url, usernameId, passwordId, submitId, username, password):
        driver = webdriver.Chrome()
        driver.get(url)
        try:
            WebDriverWait(driver,30).until(
                EC.presence_of_element_located((By.CLASS_NAME, submitId))
            )
        except Exception as e:
            print("Error encountered while login at "+url+" : ", e)
        finally:
            driver.find_element(By.ID, usernameId).send_keys(username)
            driver.find_element(By.ID, passwordId).send_keys(password)
            driver.find_element(By.CLASS_NAME, submitId).click()
            time.sleep(3)
            return driver

    # Login method for MD
    def loginMD(self, url, username, password):
        driver = webdriver.Chrome()
        driver.get(url)
        try:
            WebDriverWait(driver,30).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'LOGIN')]"))
            )
        except Exception as e:
            print("While waiting for the page of load encountered this error:", e)
        finally:
            driver.find_element(By.CLASS_NAME, "username-textbox").send_keys(username)
            driver.find_element(By.CLASS_NAME, "password-textbox").send_keys(password)
            driver.find_element(By.XPATH, "//button[contains(text(), 'LOGIN')]").click()
            time.sleep(2)
            return driver