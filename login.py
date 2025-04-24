import logging
import time
import colorama
from colorama import Fore, Style
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


LOGIN_URL = "https://portal1.fvj.br/PortalFVJ"
PORTAL_URL = "https://multi.unijaguaribe.com.br/"
WAIT_TIMEOUT = 20  # Segundos para esperar por elementos

def perform_login(driver, credentials):
    try:
        username = credentials['usuario']
        password = credentials['senha']
        
        logging.info(f"{Fore.CYAN}Navegando para a página de login: {LOGIN_URL}{Style.RESET_ALL}")
        driver.get(LOGIN_URL)
        
        wait = WebDriverWait(driver, WAIT_TIMEOUT)
        
        #login
        logging.info(f"{Fore.CYAN}Inserindo usuário e senha...{Style.RESET_ALL}")
        username_field = wait.until(EC.presence_of_element_located((By.ID, "login")))
        password_field = wait.until(EC.presence_of_element_located((By.ID, "password")))
        login_button1 = wait.until(EC.element_to_be_clickable((By.ID, "btnEntrar")))
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        logging.info(f"{Fore.CYAN}Clicando no primeiro botão 'Acessar'...{Style.RESET_ALL}")
        login_button1.click()
        
        # --- Segunda etapa do login ---
        logging.info(f"{Fore.CYAN}Aguardando o segundo botão 'Acessar'...{Style.RESET_ALL}")
        time.sleep(2)
        login_button2 = wait.until(EC.element_to_be_clickable((By.ID, "btnEntrar")))
        
        logging.info(f"{Fore.CYAN}Clicando no segundo botão 'Acessar'...{Style.RESET_ALL}")
        login_button2.click()
        
        # --- Verificação de sucesso ---
        logging.info(f"{Fore.CYAN}Aguardando confirmação do login...{Style.RESET_ALL}")
        wait.until(EC.url_to_be("https://portal1.fvj.br/PortalFVJ/Home/Index"))
        logging.info(f"{Fore.GREEN}Login inicial confirmado. Navegando para Acadêmico...{Style.RESET_ALL}")
        
        # Clicar no link ACADÊMICO
        academico_link = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@href, '/PortalFVJ/Academico/Index') and .//i[contains(@class, 'fa-graduation-cap')]]")
        ))
        academico_link.click()
        logging.info(f"{Fore.GREEN}Link ACADÊMICO clicado.{Style.RESET_ALL}")
        
        # Esperar página Acadêmico carregar
        wait.until(EC.url_contains("/PortalFVJ/Academico/Index"))
        logging.info(f"{Fore.GREEN}Página Acadêmico carregada. Clicando em Plataforma EAD...{Style.RESET_ALL}")
        
        # Clicar no botão Plataforma EAD
        plataforma_ead_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Plataforma EAD']")
        ))
        plataforma_ead_button.click()
        logging.info(f"{Fore.GREEN}Botão Plataforma EAD clicado.{Style.RESET_ALL}")
        
        # Esperar redirecionamento para a PORTAL_URL final
        wait.until(EC.url_to_be(PORTAL_URL))
        logging.info(f"{Fore.GREEN}Redirecionado com sucesso para {PORTAL_URL}.{Style.RESET_ALL}")
        
        logging.info(f"{Fore.GREEN}Login e navegação para o portal EAD concluídos.{Style.RESET_ALL}")
        return True
        
    except TimeoutException:
        logging.error(f"{Fore.RED}Tempo esgotado esperando por elementos na página de login.{Style.RESET_ALL}")
        return False
    except NoSuchElementException as e:
        logging.error(f"{Fore.RED}Elemento não encontrado durante o login: {str(e)}{Style.RESET_ALL}")
        return False
    except Exception as e:
        logging.error(f"{Fore.RED}Erro inesperado durante o login: {str(e)}{Style.RESET_ALL}")
        return False 