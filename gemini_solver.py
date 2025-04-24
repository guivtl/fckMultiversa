#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import time
import re
import colorama
from colorama import Fore, Style
import google.generativeai as genai

def configure_gemini():
    """Configura a API Gemini com a chave da API."""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logging.error(f"{Fore.RED}GEMINI_API_KEY não encontrada.{Style.RESET_ALL}")
            return False
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        logging.error(f"Erro ao configurar API Gemini: {e}")
        return False

def solve_with_gemini(question_data, max_retries=3):
    """
    Resolve uma questão usando a API Gemini.
    
    Args:
        question_data: Dicionário com {"number", "text", "options"}.
        max_retries: Número máximo de tentativas.
        
    Returns:
        str: Letra da opção (A, B, C...) ou None.
    """
    if not configure_gemini():
        return None

    try:
        question_text = question_data["text"]
        options_list = question_data["options"] # Lista de textos das opções
        
        # Gerar as letras A, B, C...
        option_letters = [chr(65 + i) for i in range(len(options_list))]

        # --- Construção do Prompt Melhorado ---
        prompt_parts = [
            "Contexto: Você é um assistente de IA altamente qualificado, especialista em diversas áreas acadêmicas, incluindo",
            "Sistemas de Informação, Ciência da Computação, Administração, Direito e áreas correlatas.",
            "Sua tarefa é analisar cuidadosamente a pergunta de múltipla escolha e as opções fornecidas abaixo.",
            "\nInstruções de Resposta:",
            "1. Determine a ÚNICA opção correta.",
            "2. Sua resposta deve consistir APENAS na LETRA MAIÚSCULA correspondente à opção correta (ex: A, B, C, D, E).",
            "3. NÃO inclua nenhuma outra palavra, texto, explicação, pontuação ou formatação na sua resposta.",
            "\n--- PERGUNTA ---",
            question_text,
            "\n--- OPÇÕES ---"
        ]
        
        for letter, option_text in zip(option_letters, options_list):
            prompt_parts.append(f"{letter}. {option_text}")
        
        prompt_parts.append("\n--- RESPOSTA (APENAS A LETRA MAIÚSCULA CORRETA) ---")
        prompt = "\n".join(prompt_parts)
        # logging.debug(f"Prompt enviado para Gemini:\n{prompt}") # Descomente para depurar o prompt
        
        # --- Configuração do Modelo --- 
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest', # Modelo especificado pelo usuário
            generation_config={
                'candidate_count': 1,
                'max_output_tokens': 5,  # Suficiente para uma letra + margem pequena
                'temperature': 0.1, # Baixa temperatura para consistência
                'top_p': 0.95, # Padrão, mas explícito
                'top_k': 1    # Força a escolha da opção mais provável
            },
            # Safety settings podem ser ajustados se necessário, mas usar padrão inicialmente
            # safety_settings=[
            #     { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
            #     # ... outros
            # ]
        )
        
        # --- Chamada da API com Retentativas --- 
        response = None
        chosen_option_letter = None
        for attempt in range(max_retries):
            logging.info(f"Chamando API Gemini (Tentativa {attempt + 1}/{max_retries})...")
            try:
                response = model.generate_content(prompt)
                
                if not response or not response.candidates:
                    logging.warning(f"API não retornou candidatos válidos (Tentativa {attempt + 1}).")
                    if response and hasattr(response, 'prompt_feedback'):
                        logging.warning(f"  Feedback: {response.prompt_feedback}")
                    time.sleep(1 * (attempt + 1)) # Backoff exponencial simples
                    continue
                
                raw_answer = response.text.strip()
                if not raw_answer:
                    logging.warning(f"API retornou resposta vazia (Tentativa {attempt + 1}).")
                    if hasattr(response.candidates[0], 'finish_reason') and response.candidates[0].finish_reason:
                         logging.warning(f"  Motivo: {response.candidates[0].finish_reason}")
                    time.sleep(1 * (attempt + 1))
                    continue
                
                # Extrair APENAS a primeira letra maiúscula encontrada
                match = re.search(r'([A-Z])', raw_answer) 
                if match:
                    extracted_letter = match.group(1)
                    if extracted_letter in option_letters:
                        chosen_option_letter = extracted_letter
                        logging.info(f"{Fore.GREEN}Resposta da API: '{raw_answer}'. Letra válida extraída: {chosen_option_letter}{Style.RESET_ALL}")
                        break # Sucesso, sair do loop de retentativas
                    else:
                         logging.warning(f"Letra extraída '{extracted_letter}' não está entre as opções válidas {option_letters} (Tentativa {attempt + 1}). Resposta: '{raw_answer}'")
                else:
                    logging.warning(f"Nenhuma letra maiúscula encontrada na resposta '{raw_answer}' (Tentativa {attempt + 1}).")
            
            except Exception as e:
                logging.error(f"Erro na chamada API (Tentativa {attempt + 1}): {e}")
                if response and hasattr(response, 'prompt_feedback'):
                    logging.error(f"  Feedback: {response.prompt_feedback}")
            
            # Se chegou aqui, a tentativa falhou ou a resposta foi inválida
            if attempt < max_retries - 1:
                 time.sleep(1.5 * (attempt + 1)) # Backoff antes da próxima tentativa
        
        # --- Resultado Final --- 
        if chosen_option_letter:
            return chosen_option_letter
        else:
            logging.error(f"Falha ao obter resposta válida da API após {max_retries} tentativas.")
            return None
        
    except Exception as e:
        logging.exception(f"Erro fatal em solve_with_gemini: {e}") # Logar com traceback
        return None 