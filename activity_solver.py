#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import colorama
from colorama import Fore, Style
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ( # Importações agrupadas
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
import re
from bs4 import BeautifulSoup
import traceback

# Importações locais
from question_extractor import extract_question_data
from gemini_solver import solve_with_gemini

# --- Funções Auxiliares --- 

def print_question_debug_info(q_number, q_text, q_options):
    """Exibe informações de depuração sobre a questão atual (simplificado)."""
    logging.info(f"{Style.DIM} Q{q_number or 'N/A'}: {q_text[:80]}... | Opções: {list(q_options.keys()) if q_options else 'Nenhuma'}{Style.RESET_ALL}")

def submit_answer(driver, selected_option_element):
    """Seleciona a opção de rádio fornecida. Retorna True/False."""
    try:
        driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", selected_option_element)
        time.sleep(0.1) # Reduzido
        driver.execute_script("arguments[0].click();", selected_option_element)
        time.sleep(0.2) # Reduzido
        return True
    except StaleElementReferenceException:
        logging.warning("Opção obsoleta. Retentando seleção...")
        time.sleep(0.5)
        try:
            driver.execute_script("arguments[0].scrollIntoViewIfNeeded(true);", selected_option_element)
            time.sleep(0.1)
            driver.execute_script("arguments[0].click();", selected_option_element)
            logging.info("Seleção refeita.")
            return True
        except Exception as e_retry:
            logging.error(f"Erro na retentativa de seleção: {e_retry}")
            return False
    except Exception as e:
        logging.error(f"Erro ao selecionar opção: {e}")
        return False

def wait_for_next_question(driver, current_container):
    """Espera brevemente para dar tempo da interface atualizar o conteúdo."""
    try:
        time.sleep(1.2) # Ajustado
        driver.execute_script("return document.readyState")
        time.sleep(0.2) # Ajustado
        return True
    except Exception as e:
        logging.error(f"Erro ao aguardar atualização: {e}")
        return False

def get_total_questions(driver):
    """Obtém o número total de questões na atividade."""
    total = 5 # Padrão se outras falharem
    wait_time = 3 # Tempo de espera curto para elementos
    try:
        # 1. Tentar pelo contador de progresso
        try:
            progress_element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".progress-count"))
            )
            progress_text = progress_element.text.strip()
            match = re.search(r'(\d+)\s*(?:/|de)\s*(\d+)', progress_text)
            if match:
                total_detected = int(match.group(2))
                logging.info(f"Total detectado (progresso): {total_detected}")
                return total_detected
        except TimeoutException:
            pass # Ignora se não encontrar
            
        # 2. Tentar contar containers de questão visíveis/com corpo
        try:
             # Usar page_source para análise estática rápida
             soup = BeautifulSoup(driver.page_source, 'lxml')
             question_containers = soup.find_all("div", class_="question-content")
             valid_containers = [c for c in question_containers if c.find("div", class_="question-body")]
             if len(valid_containers) > 0:
                logging.info(f"Total detectado (containers): {len(valid_containers)}")
                return len(valid_containers)
        except Exception:
             pass # Ignora erros de parsing

        logging.warning(f"Não foi possível detectar total. Usando padrão: {total}")
        return total
        
    except Exception as e:
        logging.error(f"Erro geral ao obter total: {e}. Usando padrão: {total}")
        return total

# --- FUNÇÃO PRINCIPAL DE RESOLUÇÃO --- 

def solve_activity_questions(driver, api_key=None, max_retries_per_question=2):
    """Tenta resolver, confirma e analisa os resultados questão por questão."""
    logging.info("Iniciando tentativa de resolução da atividade...")
    activity_successful = True
    total_questions = 0 # Será definido no início
    
    try:
        total_questions = get_total_questions(driver)
        answered_count = 0
        
        while answered_count < total_questions:
            current_q_num = answered_count + 1
            logging.info(f"{Style.BRIGHT}--- Questão {current_q_num}/{total_questions} ---{Style.RESET_ALL}")
            retries = 0
            question_processed = False
            
            while retries < max_retries_per_question and not question_processed:
                time.sleep(0.3) # Pausa antes de extrair
                q_number, q_text, q_options, q_container_element = extract_question_data(driver)
                
                if q_text and q_options and q_container_element:
                    # print_question_debug_info(q_number, q_text, q_options) # Debug
                    question_data = { "number": q_number, "text": q_text, "options": [q_options[key]["text"] for key in sorted(q_options.keys())] }
                    logging.info("Consultando Gemini...")
                    chosen_letter = solve_with_gemini(question_data)
                    
                    if chosen_letter and chosen_letter in q_options:
                        logging.info(f"{Fore.GREEN}Gemini -> {chosen_letter}{Style.RESET_ALL}")
                        selected_option_element = q_options[chosen_letter]['element']
                        if submit_answer(driver, selected_option_element):
                            answered_count += 1
                            question_processed = True
                            # --- Clicar no botão "Próximo" ou "Enviar" --- 
                            try:
                                wait = WebDriverWait(driver, 5) # Tempo curto para botão
                                if answered_count < total_questions:
                                    # logging.info("Clicando em 'Próximo'...") # Reduzir log
                                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Próximo')]]")))
                                    driver.execute_script("arguments[0].click();", next_button)
                                    wait_for_next_question(driver, q_container_element)
                                else:
                                    logging.info("Última questão respondida. Clicando em 'Enviar respostas'...")
                                    submit_button_1 = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Enviar respostas')]]")))
                                    driver.execute_script("arguments[0].click();", submit_button_1)
                                    logging.info(f"{Fore.GREEN}Botão 'Enviar respostas' (1) clicado.{Style.RESET_ALL}")
                            except TimeoutException:
                                btn = "Próximo" if answered_count < total_questions else "Enviar respostas"
                                logging.error(f"Timeout: Botão '{btn}' não encontrado.")
                                activity_successful = False; break 
                            except Exception as click_err:
                                btn = "Próximo" if answered_count < total_questions else "Enviar respostas"
                                logging.error(f"Erro ao clicar '{btn}': {click_err}")
                                activity_successful = False; break
                        else:
                            logging.warning(f"Falha ao SELECIONAR opção {chosen_letter}. Tentando novamente...")
                            retries += 1; time.sleep(0.5)
                    elif chosen_letter:
                        logging.warning(f"Gemini retornou '{chosen_letter}' (inválida). Tentando novamente...")
                        retries += 1; time.sleep(1)
                    else:
                        logging.warning(f"Gemini falhou. Tentando novamente...")
                        retries += 1; time.sleep(1)
                else:
                    logging.warning(f"Falha na extração (tentativa {retries+1}). Aguardando...")
                    retries += 1; time.sleep(1.5)
            
            # Se falhou em processar esta questão após retries
            if not question_processed and activity_successful:
                logging.error(f"Não foi possível processar Questão {current_q_num}. Abortando atividade.")
                activity_successful = False
            # Se erro no clique do botão, sair do loop principal
            if not activity_successful: break 
        
        # --- Pós-Loop de Respostas --- 
        
        # Se todas as questões foram respondidas com sucesso, lidar com popup e análise
        if activity_successful:
            try:
                logging.info("Esperando popup de confirmação...")
                wait_popup = WebDriverWait(driver, 8)
                confirm_button_xpath = "//div[contains(@class, 'v-dialog--active')]//button[.//span[contains(text(), 'Enviar respostas') or contains(text(), 'Sim') or contains(text(), 'Confirmar')]]"
                confirm_button = wait_popup.until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath)))
                logging.info(f"{Fore.GREEN}Confirmando envio...{Style.RESET_ALL}")
                driver.execute_script("arguments[0].click();", confirm_button)
                
                logging.info("Aguardando carregamento dos resultados (Q1)...")
                time.sleep(1.5)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((
                    By.XPATH, "(//span[contains(@class, 'correct-answer-indicator')] | //span[contains(@class, 'incorrect-answer-indicator')] | //div[contains(@class, 'exercises-completed-date')])[1]"
                )))
                logging.info(f"{Fore.GREEN}Resultados carregados. Iniciando análise...{Style.RESET_ALL}")
                # Chama a análise questão a questão
                activity_successful = analyze_completed_activity(driver, total_questions) 

            except TimeoutException:
                logging.error("Timeout no popup de confirmação ou ao esperar resultados (Q1).")
                activity_successful = False
            except Exception as e:
                logging.error(f"Erro na confirmação/espera de resultados: {e}")
                activity_successful = False
        # Se não respondeu tudo ou erro anterior
        else:
             logging.warning("Resolução abortada ou incompleta. Análise não realizada.")

        return activity_successful
        
    except Exception as e:
        logging.exception(f"Erro inesperado em solve_activity_questions: {e}")
        return False

# --- FUNÇÕES DE ANÁLISE DE ATIVIDADE CONCLUÍDA --- 

def analyze_single_completed_question(driver, question_index):
    """Analisa o resultado da questão visível. Retorna 'correct', 'incorrect', 'unknown'."""
    result = 'unknown'
    try:
        # Análise rápida com BeautifulSoup para evitar waits desnecessários
        soup = BeautifulSoup(driver.page_source, 'lxml')
        active_container_soup = next((c for c in soup.find_all("div", class_="question-content") 
                                      if c.find("div", class_="question-body")), None)
        if not active_container_soup:
            logging.warning(f"Q{question_index+1}: Container ativo não encontrado na análise.")
            return result
        # Indicadores podem variar, checar ambos texto e classes
        correct_indicator = active_container_soup.find("span", string=re.compile(r'Você acertou!'))
        incorrect_indicator = active_container_soup.find("span", string=re.compile(r'Você não acertou!'))
        correct_wrapper = active_container_soup.find("div", class_="correctAnswer")
        incorrect_wrapper = active_container_soup.find("div", class_="incorrectAnswer")
        if correct_indicator or correct_wrapper: result = 'correct'
        elif incorrect_indicator or incorrect_wrapper: result = 'incorrect'
    except Exception as e:
        logging.error(f"Erro ao analisar Q{question_index+1}: {e}")
    return result

def analyze_completed_activity(driver, total_questions=None):
    """
    Orquestra a análise de uma atividade concluída, navegando questão por questão.
    Recebe total_questions para evitar re-calcular.
    """
    logging.info("Iniciando análise dos resultados questão por questão...")
    # Se total_questions não foi passado, tenta obter
    if total_questions is None:
         total_questions = get_total_questions(driver)
         if total_questions is None: # Se ainda assim falhar
              logging.error("Não foi possível determinar o total de questões para análise.")
              return False
              
    correct_count = 0
    incorrect_count = 0
    unknown_count = 0
    analysis_successful = True
    
    for i in range(total_questions):
        q_num = i + 1
        log_header = f"Analisando Q{q_num}/{total_questions}"
        logging.info(f"{Style.BRIGHT}{log_header}{Style.RESET_ALL}")
        time.sleep(0.2) 
        question_result = analyze_single_completed_question(driver, i)
        
        if question_result == 'correct':
            logging.info(f"{Fore.GREEN} -> Resultado: CORRETO{Style.RESET_ALL}")
            correct_count += 1
        elif question_result == 'incorrect':
            logging.info(f"{Fore.RED} -> Resultado: INCORRETO{Style.RESET_ALL}")
            incorrect_count += 1
        else:
            logging.warning(f"{Fore.YELLOW} -> Resultado: DESCONHECIDO{Style.RESET_ALL}")
            unknown_count += 1
            
        # Clicar em Próximo, se não for a última questão da análise
        if i < total_questions - 1:
            try:
                wait = WebDriverWait(driver, 3) # Espera curta pelo botão
                next_button = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//button[.//span[contains(text(), 'Próximo')]]"
                )))
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(1.2) # Espera curta para próxima questão
            except TimeoutException:
                logging.error(f"Timeout: Botão 'Próximo' não encontrado após Q{q_num}. Abortando análise.")
                analysis_successful = False; break
            except Exception as e:
                logging.error(f"Erro ao clicar 'Próximo' após Q{q_num}: {e}. Abortando.")
                analysis_successful = False; break
                
    # Log final do resumo da análise
    logging.info(f"{Fore.CYAN}--- Resumo da Análise ---{Style.RESET_ALL}")
    if analysis_successful:
        logging.info(f"{Fore.GREEN}Corretas: {correct_count}{Style.RESET_ALL}")
        logging.info(f"{Fore.RED}Incorretas: {incorrect_count}{Style.RESET_ALL}")
        if unknown_count > 0: logging.warning(f"{Fore.YELLOW}Desconhecidas: {unknown_count}{Style.RESET_ALL}")
        logging.info(f"{Fore.CYAN}Total Verificado: {total_questions}{Style.RESET_ALL}")
    else:
        logging.error("Análise não finalizada devido a erro.")
        
    return analysis_successful 