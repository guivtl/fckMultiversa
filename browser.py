#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import colorama
from colorama import Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def setup_browser():
    """
    Configura e retorna uma instância do WebDriver do Chrome.
    
    Returns:
        webdriver.Chrome: Instância do navegador ou None em caso de erro.
    """
    try:
        logging.info(f"{Fore.CYAN}Configurando navegador...{Style.RESET_ALL}")
        
        # Suprimir mensagens do webdriver-manager
        os.environ['WDM_LOG_LEVEL'] = '0'
        os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
        
        # Configuração das opções do Chrome
        options = webdriver.ChromeOptions()
        
        # Opções para dificultar a detecção
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("start-maximized")  # Garante que a janela esteja maximizada
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--log-level=3")  # Apenas erros fatais
        options.add_argument("--silent")
        
        # Previne detecção de automação (pode não ser 100% eficaz)
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Configurar user-agent comum
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        # Suprimir logs do ChromeDriver
        service = Service(
            ChromeDriverManager().install(),
            log_output=os.devnull
        )
        
        # Inicializar o navegador
        driver = webdriver.Chrome(service=service, options=options)
        
        # Script para ajudar a evitar detecção
        driver.execute_script('''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        ''')
        
        logging.info(f"{Fore.GREEN}Navegador configurado com sucesso!{Style.RESET_ALL}")
        return driver
        
    except Exception as e:
        logging.error(f"{Fore.RED}Erro ao configurar o WebDriver: {str(e)}{Style.RESET_ALL}")
        logging.error(f"{Fore.YELLOW}Verifique se o Chrome está instalado e o ChromeDriver é compatível.{Style.RESET_ALL}")
        return None 