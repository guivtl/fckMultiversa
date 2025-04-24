#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
import traceback
import colorama
from colorama import Fore, Style
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ( # Importações agrupadas
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)

# A função get_total_questions foi movida para activity_solver.py

def _find_active_question_elements(driver, soup):
    """Encontra o container soup ativo e o elemento selenium correspondente."""
    question_container_soup = None
    active_question_div_selenium = None
    try:
        all_question_divs_selenium = driver.find_elements(By.CSS_SELECTOR, "div.question-content")
        for i, container_div in enumerate(soup.find_all("div", class_="question-content")):
            # A questão ativa tem um corpo (não está vazia)
            if container_div.find("div", class_="question-body"): 
                question_container_soup = container_div
                if i < len(all_question_divs_selenium):
                    active_question_div_selenium = all_question_divs_selenium[i]
                    logging.info(f"Container da questão ativa encontrado (índice HTML {i}).")
                    break # Encontrou o ativo
                else:
                    logging.warning(f"Discrepância entre soup e selenium (índice {i}).")
                    # Pode tentar buscar pelo selenium se houver discrepância?
                    if all_question_divs_selenium:
                         logging.info("Tentando localizar o ativo via Selenium...")
                         for sel_div in all_question_divs_selenium:
                              if sel_div.is_displayed():
                                   active_question_div_selenium = sel_div
                                   # Atualizar o soup para corresponder? (complexo)
                                   logging.info("Container ativo localizado via Selenium.")
                                   break
                         if active_question_div_selenium:
                              break # Sai do loop externo
    except Exception as e:
        logging.error(f"Erro ao buscar container ativo: {e}")
    return question_container_soup, active_question_div_selenium

def _extract_question_number(soup, question_container_soup):
    """Extrai o número da questão a partir do soup."""
    try:
        # 1. Tentar pelo progresso geral
        progress_span = soup.find("span", class_="progress-count")
        if progress_span and progress_span.strong:
            return int(progress_span.strong.text.strip())
        # 2. Tentar pelo identificador dentro da questão
        if question_container_soup:
             identifier_span = question_container_soup.find("span", class_="question-identifier")
             if identifier_span:
                 match = re.search(r'(\d+)', identifier_span.text)
                 if match:
                     return int(match.group(1))
    except Exception as e:
        logging.warning(f"Não foi possível extrair número da questão: {e}")
    return None # Retorna None se não encontrar

def _extract_question_text(question_container_soup):
    """Extrai o texto da questão a partir do container soup ativo."""
    try:
        text_div = question_container_soup.find("div", class_="question-text")
        if text_div:
             # Prioriza pegar parágrafos dentro de 'question-text'
             paragraphs = text_div.find_all("p")
             text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
             if text: return text
             # Se não achar parágrafos, pega o texto da div inteira
             return text_div.get_text(separator='\n', strip=True)
        # Plano B: div com classe 'question'
        question_div = question_container_soup.find("div", class_="question")
        if question_div:
            return question_div.get_text(separator='\n', strip=True)
        # Plano C: Pega todo texto do corpo da questão
        body_div = question_container_soup.find("div", class_="question-body")
        if body_div:
             return body_div.get_text(separator='\n', strip=True) # Pode incluir texto das opções
    except Exception as e:
        logging.error(f"Erro ao extrair texto da questão: {e}")
    return ""

def _extract_options(driver, question_container_soup, active_question_div_selenium):
    """Extrai as opções (texto e elemento selenium) do container ativo."""
    options_dict = {}
    try:
        option_divs = question_container_soup.find_all("div", class_="option")
        if not option_divs:
             logging.warning("Nenhuma div.option encontrada no container.")
             return options_dict
             
        logging.info(f"Encontradas {len(option_divs)} divs de opção para processar.")
        all_radios_in_selenium_container = active_question_div_selenium.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
        for i, option_div in enumerate(option_divs):
            option_letter = chr(65 + i)
            option_text = ""
            radio_element_selenium = None
            
            # 1. Extrair texto da opção (várias tentativas)
            try:
                option_body = option_div.find("div", class_="question-option")
                if option_body: option_text = option_body.get_text(separator='\n', strip=True)
                if not option_text:
                    label = option_div.find("label", class_="option-label")
                    if label:
                        option_text = label.get_text(separator='\n', strip=True)
                        option_text = re.sub(r'^[A-Z][.,)]?\s*', '', option_text).strip() # Remove A. B)
            except Exception as e_text:
                 logging.warning(f"Erro extraindo texto da Opção {option_letter}: {e_text}")
            option_text = option_text or f"Opção {option_letter} (sem texto)"
                 
            # 2. Encontrar o elemento Selenium clicável (rádio)
            try:
                radio_soup = option_div.find("input", type="radio")
                if radio_soup and radio_soup.has_attr('id'):
                    radio_id = radio_soup['id']
                    try:
                        # Busca OTIMIZADA dentro do container selenium ativo
                        radio_element_selenium = active_question_div_selenium.find_element(By.ID, radio_id)
                        # logging.info(f" Selenium para Opção {option_letter} via ID: {radio_id}") # Log Reduzido
                    except NoSuchElementException:
                        logging.warning(f" ID {radio_id} (Opção {option_letter}) não encontrado via Selenium, tentando índice...")
                        # Fallback para índice se ID falhar (menos confiável)
                        if i < len(all_radios_in_selenium_container):
                             radio_element_selenium = all_radios_in_selenium_container[i]
                             logging.info(f" Selenium para Opção {option_letter} via índice.")
                elif i < len(all_radios_in_selenium_container):
                     # Se não achou ID no soup, tenta pegar pelo índice do Selenium direto
                     radio_element_selenium = all_radios_in_selenium_container[i]
                     logging.info(f" Selenium para Opção {option_letter} via índice (sem ID no soup).")
                     
                if not radio_element_selenium:
                     logging.error(f"Não foi possível localizar elemento Selenium clicável para Opção {option_letter}.")
                     
            except Exception as e_sel:
                logging.error(f"Erro buscando elemento Selenium para Opção {option_letter}: {e_sel}")
                
            # Adicionar ao dicionário SOMENTE se encontrou o elemento clicável
            if radio_element_selenium:
                options_dict[option_letter] = {
                    'text': option_text,
                    'element': radio_element_selenium # O importante é ter o elemento clicável
                }
            else:
                logging.error(f"Opção {option_letter} ignorada (sem elemento Selenium). Texto: {option_text[:50]}...")
                
    except Exception as e:
        logging.error(f"Erro geral ao processar opções: {e}")
        
    return options_dict

def extract_question_data(driver):
    """Extrai dados da questão visível (refatorado)."""
    question_number = None
    question_text = ""
    options_dict = {}
    active_question_div_selenium = None 
    
    try:
        # Espera e obtém HTML
        WebDriverWait(driver, 5).until(lambda d: d.execute_script("return document.readyState") == "complete")
        logging.info("Obtendo HTML da página...")
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        # Encontra container ativo (soup e selenium)
        question_container_soup, active_question_div_selenium = _find_active_question_elements(driver, soup)
        if not question_container_soup or not active_question_div_selenium:
            return None, None, None, None # Falha crítica se não achar o container
        
        # Extrai número, texto e opções usando funções auxiliares
        question_number = _extract_question_number(soup, question_container_soup)
        question_text = _extract_question_text(question_container_soup)
        options_dict = _extract_options(driver, question_container_soup, active_question_div_selenium)
            
        # Log final
        if options_dict:
            logging.info(f"{Fore.GREEN}Extração concluída: Q{question_number or '?'} com {len(options_dict)} opções válidas.{Style.RESET_ALL}")
        else:
            logging.error(f"{Fore.RED}Nenhuma opção válida (com elemento Selenium) encontrada!{Style.RESET_ALL}")
            
        return question_number, question_text, options_dict, active_question_div_selenium 
        
    except Exception as e:
        logging.error(f"Erro fatal em extract_question_data: {str(e)}")
        traceback.print_exc()
        return None, None, None, None 