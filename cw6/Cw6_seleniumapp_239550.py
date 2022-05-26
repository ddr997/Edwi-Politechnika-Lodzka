# Cw.6 EDWI (31.05.22) Maciej Lukaszewicz 239550, SRiPM Informatyka
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

if __name__ == "__main__":
    driver = webdriver.Chrome()
    driver.get("http://127.0.0.1:5000/")

    getForm = WebDriverWait(driver, 3).until(EC.presence_of_element_located(
        (By.XPATH, r'//input[@value="Otwórz formularz"]')
    ))
    getForm.click()

    getAnswer = driver.find_element(By.XPATH, "//p[2]").text.split(": ")[1]
    getName = driver.find_element(By.XPATH, "//p[3]").text.split(": ")[1]
    getEmail = driver.find_element(By.XPATH, "//p[4]").text.split(": ")[1]
    getPassword = driver.find_element(By.XPATH, "//p[5]").text.split(": ")[1]

    emailForm = driver.find_element(By.ID, "email")
    emailForm.send_keys(getEmail)
    nameForm = driver.find_element(By.ID, "name")
    nameForm.send_keys(getName)
    passwordForm = driver.find_element(By.ID, "password")
    passwordForm.send_keys(getPassword)
    passwordRepeatForm = driver.find_element(By.ID, "password-repeat")
    passwordRepeatForm.send_keys(getPassword)

    select = Select(driver.find_element(By.ID, "answer"))
    select.select_by_visible_text(getAnswer)

    time.sleep(2)  # prezentacja wypelnienia formularza

    submit = driver.find_element(By.XPATH, '//*[@type="submit"]')
    submit.click()
