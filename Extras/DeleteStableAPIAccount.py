from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time 

class DeleteStableAPIAccount:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        self.driver = webdriver.Chrome(options=chrome_options)
        self.vars = {}

    def start(self, email_addr, password):
        self.driver.get("https://platform.stability.ai/")
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        
        time.sleep(2)
        self.driver.find_element(By.ID, "username").send_keys(email_addr)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.NAME, "action").click()  
        time.sleep(1)      

        self.driver.get("https://platform.stability.ai/account/overview")
        time.sleep(3)
        buttons = self.driver.find_elements(By.CLASS_NAME, 'h-fit')
        buttons[1].click()
        time.sleep(3)
        cnf_buttons = self.driver.find_elements(By.CLASS_NAME, 'h-fit')
        cnf_buttons[3].click()

if __name__ == "__main__":
    test = DeleteStableAPIAccount()
    test.start("kediga6622@hdrlog.com", "test@123")