import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from EmailGenerator import EmailGenerator
from AddToDB import AddToDB

class StableAPIGen():
    def setup_method(self):
        self.email = EmailGenerator()
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        self.driver = webdriver.Chrome(options=chrome_options)
        self.vars = {}
    
    def start(self):
        self.driver.get("https://platform.stability.ai/")
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.LINK_TEXT, "Sign up").click()
        
        email_addr = self.email.create_email()
        password   = "Test@12345"
        self.driver.find_element(By.ID, "email").send_keys(email_addr)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.NAME, "action").click()

        time.sleep(10)
        recent_email_link = self.get_verification_link()
        print(recent_email_link)
        self.driver.get(recent_email_link)

        wait = WebDriverWait(self.driver, 30)
        action_button = wait.until(EC.element_to_be_clickable((By.NAME, "action")))
        action_button.click()

        self.driver.get("https://platform.stability.ai/account/keys")
        outer_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="grid w-full grid-cols-5 items-center border-b border-white/5 last-of-type:border-none"]'))
        )
        flex_div = outer_div.find_element(By.XPATH, './/div[@class="flex justify-end"]')
        buttons = flex_div.find_elements(By.CLASS_NAME, 'h-fit')
        if len(buttons) >= 2:
            buttons[1].click()
        else:
            print("Second button not found.")

        api_key_div = self.driver.find_element(By.XPATH, '//div[@class="col-span-3 text-left font-mono"]/div[@class="truncate"]')
        api_key = api_key_div.text
        print(f"API Key: {api_key}")
        self.logout()
        return api_key, email_addr, password
    
    def get_verification_link(self):
        recent_email_link = self.email.get_recent_email_link()
        if recent_email_link:
            return recent_email_link
        else:
            time.sleep(2)
            self.get_verification_link

    def logout(self):
        self.driver.get("https://platform.stability.ai/logout")
        
if __name__ == "__main__":
    add = AddToDB()
    test = StableAPIGen()
    test.setup_method()
    for i in range(10):
        api_key, email_addr, password = test.start()
        add.start(api_key, email_addr, password)
        time.sleep(2)
