#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import colorama
from colorama import Fore, Style
import os
import warnings
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

# Desativa warnings e logs menos importantes
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
os.environ['WDM_LOG_LEVEL'] = '0' # Desativa logs do webdriver-manager
os.environ['WDM_PRINT_FIRST_LINE'] = 'False'

# Importações do projeto
from config import load_env_variables
from browser import setup_browser
from login import perform_login
from course_processor import process_course
from dashboard_parser import extract_courses

# Configuração inicial do colorama
colorama.init(autoreset=True)

# Configuração de logging mais estruturada
# Formato: [NÍVEL] Mensagem (com cores)
class CustomFormatter(logging.Formatter):
    grey = Style.DIM
    blue = Fore.BLUE + Style.BRIGHT
    yellow = Fore.YELLOW + Style.BRIGHT
    red = Fore.RED + Style.BRIGHT
    bold_red = Fore.RED + Style.BRIGHT
    green = Fore.GREEN + Style.BRIGHT
    reset = Style.RESET_ALL

    FORMATS = {
        logging.DEBUG: grey + "[DBUG]" + reset + " %(message)s",
        logging.INFO: blue + "[INFO]" + reset + " %(message)s",
        logging.WARNING: yellow + "[WARN]" + reset + " %(message)s",
        logging.ERROR: red + "[ERR] " + reset + "%(message)s",
        logging.CRITICAL: bold_red + "[CRIT]" + reset + " %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Criar logger principal
logger = logging.getLogger()
logger.setLevel(logging.INFO) # Nível principal

# Remover handlers existentes para evitar duplicação
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
    
# Adicionar handler de console com o novo formatador
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO) # Mostrar INFO e acima no console
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)

# Silenciar loggers de bibliotecas externas (nível ERROR)
external_loggers = [
    'urllib3', 'selenium', 'WDM', 'tensorflow', 'libdevice', 
    'webdriver_manager', 'chromium', 'h5py'
]
for logger_name in external_loggers:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Função auxiliar para imprimir separadores
def print_separator(char='-', length=50):
    print(f"{Fore.YELLOW}{char * length}{Style.RESET_ALL}")

def print_header(title):
    print_separator()
    print(f"{Style.BRIGHT}{Fore.CYAN} {title} {Style.RESET_ALL}")
    print_separator()

def get_user_course_selection(available_courses):
    """Apresenta os cursos e pede a seleção do usuário."""
    if not available_courses:
        return []

    print_header("Cursos Encontrados")
    for i, course in enumerate(available_courses):
        print(f"  {Style.BRIGHT}{i+1}{Style.RESET_ALL}. {course['name']}")
    print_separator()

    while True:
        try:
            choice = input(f" {Style.BRIGHT}Digite os números dos cursos (ex: 1, 3, 5), 'all' para todos, ou 'q' para sair: {Style.RESET_ALL}").strip().lower()
            
            if choice == 'q':
                return [] # Sair
            if choice == 'all':
                return available_courses # Todos os cursos
            
            # Processar números individuais ou separados por vírgula
            selected_indices = []
            parts = choice.split(',')
            for part in parts:
                num_str = part.strip()
                if num_str.isdigit():
                    index = int(num_str) - 1 # Converter para índice 0-based
                    if 0 <= index < len(available_courses):
                        selected_indices.append(index)
                    else:
                        print(f" {Fore.RED}Número inválido: {num_str}. Tente novamente.{Style.RESET_ALL}")
                        raise ValueError # Força repetição do loop
                else:
                     print(f" {Fore.RED}Entrada inválida: '{num_str}'. Use números, 'all' ou 'q'.{Style.RESET_ALL}")
                     raise ValueError # Força repetição do loop
            
            # Remover duplicatas e ordenar
            selected_indices = sorted(list(set(selected_indices)))
            
            # Construir lista de cursos selecionados
            selected_courses = [available_courses[i] for i in selected_indices]
            
            print(f" {Fore.GREEN}Cursos selecionados:{Style.RESET_ALL}")
            for course in selected_courses:
                print(f"   - {course['name']}")
            confirm = input(f" {Style.BRIGHT}Confirmar seleção? (s/n): {Style.RESET_ALL}").strip().lower()
            if confirm == 's':
                 return selected_courses
            else:
                 print(" Seleção cancelada. Tente novamente.")
                 # Continua no loop while

        except ValueError:
            continue # Pede input novamente
        except Exception as e:
            logging.error(f"Erro inesperado na seleção: {e}")
            return [] # Retorna vazio em caso de erro grave

def main():
    """Função principal que orquestra o processo."""
    print_header("Iniciando MultiversaBypass")
    
    credentials = load_env_variables()
    if not credentials:
        logging.error(f"{Fore.RED}Falha ao carregar credenciais do .env")
        return
    logging.info(f"Credenciais carregadas.")
    
    driver = setup_browser()
    if not driver:
        logging.error(f"{Fore.RED}Falha ao configurar navegador.")
        return
    logging.info(f"Navegador configurado.")
    
    try:
        print_header("Processo de Login")
        logging.info("Iniciando login...")
        if not perform_login(driver, credentials):
            logging.error(f"{Fore.RED}Falha no login.")
            return
        logging.info(f"{Fore.GREEN}Login bem-sucedido.{Style.RESET_ALL}")
        
        # Navegar para a página inicial/dashboard após login (ajuste a URL se necessário)
        dashboard_url = credentials.get("MOODLE_URL", "https://multi.unijaguaribe.com.br/") 
        if not dashboard_url.endswith('/'): dashboard_url += '/'
        # Tentativas comuns de dashboard
        possible_dashboards = [dashboard_url + "my/", dashboard_url]
        logged_in_dashboard_url = None
        for url in possible_dashboards:
             try:
                 logging.info(f"Tentando acessar dashboard: {url}")
                 driver.get(url)
                 WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.coursebox, div[data-region='course-list-item']")))
                 logged_in_dashboard_url = url # Encontrou um dashboard válido
                 logging.info(f"Dashboard acessado em: {url}")
                 break
             except TimeoutException:
                 logging.warning(f"Dashboard não encontrado ou sem cursos em {url}")
                 continue
             except Exception as e:
                 logging.error(f"Erro ao acessar {url}: {e}")
                 continue
                 
        if not logged_in_dashboard_url:
            logging.error("Não foi possível encontrar a página de cursos após o login.")
            return

        # Extrair cursos
        available_courses = extract_courses(driver)
        if not available_courses:
            logging.error("Nenhum curso encontrado para processar.")
            return
            
        # Obter seleção do usuário
        selected_courses = get_user_course_selection(available_courses)
        
        if not selected_courses:
            logging.info("Nenhum curso selecionado. Encerrando.")
        else:
            print_header("Iniciando Processamento dos Cursos Selecionados")
            # Iterar sobre os cursos selecionados
            for i, course in enumerate(selected_courses):
                logging.info(f"{Style.BRIGHT}Processando Curso {i+1}/{len(selected_courses)}: {course['name']}{Style.RESET_ALL}")
                process_course(driver, course['url']) # Passa a URL do curso
                print_separator('=') # Separador entre cursos
                time.sleep(2) # Pausa entre cursos
            
            print_header("Processamento de Todos os Cursos Selecionados Concluído")

    except Exception as e:
        # Manter o log de erro crítico mais visível
        logging.exception(f"{Fore.RED}{Style.BRIGHT}Erro crítico inesperado: {str(e)}{Style.RESET_ALL}")
    finally:
        if 'driver' in locals() and driver:
            print_separator()
            logging.info("Encerrando navegador...")
            driver.quit()
            logging.info(f"{Fore.GREEN}Navegador fechado.{Style.RESET_ALL}")
        print_header("Script Finalizado")

if __name__ == "__main__":
    main() 