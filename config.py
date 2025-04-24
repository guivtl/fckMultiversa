import os
import logging
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

ENV_FILE = ".env"

def load_env_variables():
    if not os.path.exists(ENV_FILE):
        logging.error(f"{Fore.RED}Erro: Arquivo '{ENV_FILE}' não encontrado.{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}Por favor, crie um arquivo '{ENV_FILE}' com as seguintes variáveis:{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}FVJ_USERNAME=seu_usuario{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}FVJ_PASSWORD=sua_senha{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}GEMINI_API_KEY=sua_chave_api{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}Você pode copiar e renomear o arquivo '.env.example'.{Style.RESET_ALL}")
        return None
    
    load_dotenv(dotenv_path=ENV_FILE)
    

    username = os.getenv("FVJ_USERNAME")
    password = os.getenv("FVJ_PASSWORD")
    api_key = os.getenv("GEMINI_API_KEY")
    

    if not username:
        username = os.getenv("USUARIO")
    if not password:
        password = os.getenv("SENHA")
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not username or not password or not api_key:
        missing_vars = []
        if not username:
            missing_vars.append("FVJ_USERNAME/USUARIO")
        if not password:
            missing_vars.append("FVJ_PASSWORD/SENHA")
        if not api_key:
            missing_vars.append("GEMINI_API_KEY")
            
        logging.error(f"{Fore.RED}Erro: Variáveis de ambiente não definidas em '{ENV_FILE}': {', '.join(missing_vars)}{Style.RESET_ALL}")
        return None
    
    return {
        'usuario': username,
        'senha': password,
        'api_key': api_key
    } 