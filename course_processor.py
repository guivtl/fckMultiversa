#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import colorama
from colorama import Fore, Style
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from activity_navigator import navigate_to_activity_exercises
from activity_solver import solve_activity_questions, analyze_completed_activity

def process_course(driver, course_url):
    """
    Navega para a página do curso, encontra e processa cada atividade LTI.
    Se a atividade já estiver concluída, analisa os resultados existentes questão por questão.
    
    Args:
        driver: Instância do WebDriver.
        course_url: URL da página do curso.
    """
    logging.info(f"{Fore.BLUE}Navegando para o curso: {course_url}{Style.RESET_ALL}")
    try:
        driver.get(course_url)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "page-content")))
    except Exception as e:
        logging.error(f"Falha ao carregar curso {course_url}: {e}")
        return
    
    logging.info("Procurando por atividades LTI...")
    activity_links_xpath = "//li[contains(@class, 'activity') and contains(@class, 'lti')]//div[@class='activityname']/a[contains(@onclick, 'window.open') and contains(@href, '/lti/')]"
    
    try:
        activity_link_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, activity_links_xpath))
        )
        logging.info(f"{Fore.GREEN}Encontradas {len(activity_link_elements)} atividades LTI.{Style.RESET_ALL}")
    except TimeoutException:
        logging.info("Nenhuma atividade LTI encontrada.")
        activity_link_elements = []
    except Exception as e:
        logging.error(f"Erro ao procurar atividades LTI: {e}")
        activity_link_elements = []
    
    if not activity_link_elements:
        logging.info("Nenhuma atividade para processar.")
        return
    
    original_window = driver.current_window_handle
    
    for index in range(len(activity_link_elements)):
        activity_name = "N/A"
        try:
            if driver.current_window_handle != original_window: driver.switch_to.window(original_window)
            if driver.current_url != course_url: driver.get(course_url)
            
            current_activity_elements = WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH, activity_links_xpath)))
            if index >= len(current_activity_elements): continue
            current_activity_element = current_activity_elements[index]
            
            try:
                name_span = current_activity_element.find_element(By.XPATH, ".//span[contains(@class, 'instancename')]")
                activity_name = name_span.text.strip()
                accesshide_span = name_span.find_elements(By.XPATH, ".//span[contains(@class, 'accesshide')]")
                if accesshide_span: activity_name = activity_name.replace(accesshide_span[0].text.strip(), '').strip()
            except NoSuchElementException: activity_name = current_activity_element.text.strip()
                
            logging.info(f"{Fore.CYAN}--- Processando Atividade {index + 1}: '{activity_name}' ---{Style.RESET_ALL}")
            
            if activity_name in ["Biblioteca A", "Fórum", "Manual"]: 
                logging.info(f"Pulando atividade '{activity_name}'.")
                continue
                
        except (TimeoutException, IndexError, Exception) as e:
            logging.error(f"Erro ao preparar atividade {index + 1} ('{activity_name}'). Pulando. Erro: {e}")
            continue
        
        navigation_status = navigate_to_activity_exercises(driver, current_activity_element)
        
        if navigation_status is True:
            logging.info("Iniciando resolução...")
            solve_success = solve_activity_questions(driver)
            if solve_success:
                logging.info(f"{Fore.GREEN}Atividade '{activity_name}' resolvida e resultados analisados.{Style.RESET_ALL}")
            else:
                logging.error(f"Falha na resolução/análise da atividade '{activity_name}'.")
        
        elif navigation_status == "COMPLETED":
            logging.info(f"{Fore.BLUE}Atividade '{activity_name}' já concluída. Analisando questão por questão...{Style.RESET_ALL}")
            # Chama a função que navega questão por questão na atividade concluída
            analyze_completed_activity(driver)
        
        else:
            logging.error(f"Falha ao acessar atividade '{activity_name}'. Pulando.")
        
        # Voltar para janela/página principal
        try:
            if len(driver.window_handles) > 1:
                for handle in driver.window_handles:
                    if handle != original_window: driver.switch_to.window(handle); driver.close()
                driver.switch_to.window(original_window)
            if driver.current_url != course_url:
                 driver.get(course_url)
                 time.sleep(0.5)
        except Exception as e:
            logging.warning(f"Erro ao gerenciar janelas/voltar ao curso: {e}")
            try: driver.get(course_url); time.sleep(1)
            except: logging.error("Falha crítica ao retornar à página do curso.")
            
        logging.info("Pausa...")
        time.sleep(1) # Pausa bem curta
    
    logging.info(f"{Fore.GREEN}--- Processamento do curso concluído ---{Style.RESET_ALL}") 