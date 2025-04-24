#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from bs4 import BeautifulSoup
from colorama import Fore, Style
import re

def extract_courses(driver):
    """
    Extrai a lista de cursos disponíveis no dashboard do usuário.

    Args:
        driver: Instância do WebDriver posicionada na página do dashboard.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um curso
              contendo 'name' e 'url'. Retorna lista vazia em caso de erro.
    """
    courses = []
    logging.info("Extraindo lista de cursos do dashboard...")
    try:
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'lxml')

        # Encontrar o container principal dos cursos
        # O seletor pode precisar de ajuste dependendo da página exata (ex: /my/ ou /)
        course_list_container = soup.find("div", class_=["courses", "frontpage-course-list-enrolled"])
        if not course_list_container:
             # Tentar outro seletor comum em dashboards Moodle
             course_list_container = soup.find("div", {"role": "list", "data-region": "course-list"})
             if not course_list_container:
                  logging.warning("Container principal da lista de cursos não encontrado.")
                  return courses # Retorna lista vazia

        # Encontrar cada caixa de curso dentro do container
        course_boxes = course_list_container.find_all("div", class_="coursebox")
        if not course_boxes:
             # Tentar outro seletor comum
             course_boxes = course_list_container.find_all("div", {"data-region": "course-list-item"})
             if not course_boxes:
                  logging.warning("Nenhuma caixa de curso ('coursebox' ou similar) encontrada.")
                  return courses

        for box in course_boxes:
            name = "Nome não encontrado"
            url = None
            try:
                # Tenta encontrar o link dentro do h3 ou h4
                link_element = box.find(["h3", "h4"], class_="coursename")
                if link_element:
                     link_element = link_element.find("a", class_="aalink") # Busca o 'a' dentro do h3/h4
                     
                # Tenta outro seletor comum se o primeiro falhar
                if not link_element:
                    link_element = box.find("a", class_="coursename") # Link diretamente com a classe
                    
                if link_element and link_element.has_attr('href'):
                    name = link_element.get_text(strip=True)
                    url = link_element['href']
                    # Remover sufixos comuns como "- ANO/SEMESTRE"
                    name = re.sub(r'\s*-\s*\d{4}\.?\d?\s*$', '', name).strip()
                    courses.append({'name': name, 'url': url})
                else:
                     logging.warning(f"Não foi possível encontrar link/nome para um curso no box: {box.prettify()[:200]}...")

            except Exception as e_inner:
                logging.warning(f"Erro processando um coursebox: {e_inner}")
                continue # Pula para o próximo curso

        if courses:
            logging.info(f"{Fore.GREEN}Encontrados {len(courses)} cursos.{Style.RESET_ALL}")
        else:
            logging.warning("Nenhum curso válido extraído da página.")

    except Exception as e:
        logging.error(f"Erro ao extrair lista de cursos: {e}")
        import traceback
        traceback.print_exc()

    return courses 