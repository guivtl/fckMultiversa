#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import time
import colorama
from colorama import Fore, Style
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

def navigate_to_activity_exercises(driver, activity_link_element):
    wait = WebDriverWait(driver, 15)
    activity_name = "N/A"
    
    try:
        # Pega o nome da atividade para logging
        try:
            activity_name = activity_link_element.find_element(By.XPATH, ".//span[contains(@class, 'instancename')]").text.strip()
        except NoSuchElementException:
            activity_name = activity_link_element.text.strip()  # Fallback
            
        logging.info(f"{Fore.CYAN}--- Tentando atividade: '{activity_name}' ---{Style.RESET_ALL}")
        
        # 1. Extrair URL do onclick
        onclick_text = activity_link_element.get_attribute("onclick")
        if not onclick_text:
            logging.error(f"{Fore.RED}Atributo 'onclick' não encontrado para a atividade '{activity_name}'.{Style.RESET_ALL}")
            return False
        
        url_match = re.search(r"window\.open\('([^']+)'", onclick_text)
        if not url_match:
            logging.error(f"{Fore.RED}Não foi possível extrair a URL do onclick: {onclick_text}{Style.RESET_ALL}")
            return False
        
        extracted_url = url_match.group(1)
        logging.info(f"{Fore.GREEN}URL extraída: {extracted_url}{Style.RESET_ALL}")
        
        # 2. Navegar para a URL na aba atual
        logging.info(f"{Fore.CYAN}Navegando para {extracted_url}...{Style.RESET_ALL}")
        driver.get(extracted_url)
        
        # 3. Esperar a página de atividade externa carregar
        wait.until(EC.url_contains("fvj.grupoa.education"))
        logging.info(f"{Fore.GREEN}Página da atividade externa carregada.{Style.RESET_ALL}")
        
        # 4. Clicar no botão/link "Exercícios"
        logging.info(f"{Fore.CYAN}Procurando e clicando no link/botão 'Exercícios'...{Style.RESET_ALL}")
        exercicios_button_xpath = "//a[.//span[@class='main-text' and normalize-space()='Exercícios']]"
        
        exercicios_button = wait.until(EC.element_to_be_clickable(
            (By.XPATH, exercicios_button_xpath)
        ))
        exercicios_button.click()
        logging.info(f"{Fore.GREEN}Link 'Exercícios' clicado.{Style.RESET_ALL}")
        
        # 5. Verificar se a atividade já foi respondida
        try:
            short_wait = WebDriverWait(driver, 3)
            completion_message_xpath = "//*[contains(text(), 'Respostas enviadas em:')]"
            completion_element = short_wait.until(
                EC.presence_of_element_located((By.XPATH, completion_message_xpath))
            )
            logging.info(f"{Fore.BLUE}Atividade '{activity_name}' já concluída: {completion_element.text}.{Style.RESET_ALL}")
            return "COMPLETED"  # Indica conclusão, sem fechar aba
        except TimeoutException:
            logging.info(f"{Fore.GREEN}Mensagem de conclusão não encontrada. Prosseguindo...{Style.RESET_ALL}")
            pass  # Continua
        
        # 6. Esperar a seção de exercícios carregar
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.question-content")))
        logging.info(f"{Fore.GREEN}Seção de exercícios carregada com sucesso.{Style.RESET_ALL}")
        return True
    
    except TimeoutException:
        logging.error(f"{Fore.RED}Tempo esgotado ao tentar acessar exercícios da atividade '{activity_name}'.{Style.RESET_ALL}")
        return False
    except NoSuchElementException:
        logging.error(f"{Fore.RED}Elemento não encontrado ao tentar acessar exercícios da atividade '{activity_name}'.{Style.RESET_ALL}")
        return False
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao tentar acessar exercícios da atividade '{activity_name}': {str(e)}{Style.RESET_ALL}")
        return False 