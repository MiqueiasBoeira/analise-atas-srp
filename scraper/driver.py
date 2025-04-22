"""
Abstração do driver Selenium: conexão ao Chrome existente e helpers de espera/navegação.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config


def conectar_driver():
    """
    Conecta ao Chrome já aberto com --remote-debugging-port.
    O usuário deve abrir o Chrome manualmente e fazer login no portal antes.
    """
    chrome_options = Options()
    chrome_options.debugger_address = config.CHROME_DEBUG_ADDRESS
    if config.CHROMEDRIVER_PATH:
        service = Service(config.CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)
    return driver


def abrir_nova_aba(driver, url: str) -> None:
    """Abre uma nova aba e navega para a URL (não interfere na aba manual)."""
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(url)


def esperar(driver, xpath: str, timeout: int = 20):
    """Aguarda até que o elemento exista no DOM."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
