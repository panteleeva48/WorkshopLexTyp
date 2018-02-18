#!/usr/bin/env python
# -*- coding: utf-8 -*-
import conf
import google.cloud.translate
import google.oauth2.service_account
import json
import requests
from definitions import GOOGLE_TRANSLATION_ATTR, YANDEX_TRANSLATION_ATTR, YANDEX_TRANSLATE_REQUEST
from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException



def wait_for_element_to_load(driver, by_tag, by_cont):
    try:
        element_present = EC.presence_of_all_elements_located((by_tag, by_cont))
        WebDriverWait(driver, 10).until(element_present)
    except TimeoutException:
        raise TimeoutError('Oops!')

def google_synonym_tranlate(to_translate, source_language, target_language):
    driver = webdriver.Chrome()
    query = 'https://translate.google.com/?#'+'/'.join([source_language, target_language, to_translate])
    print(query)
    driver.get(query)

    try:
        wait_for_element_to_load(driver, By.XPATH, '//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[3]/span[2]')
        driver.find_element_by_xpath('//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[3]/span[2]').click()
    except selenium.common.exceptions.ElementNotVisibleException:
        pass
    wait_for_element_to_load(driver, By.XPATH, '//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[2]/table')
    try:
        table = driver.find_element_by_xpath('//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[2]/table')
    except selenium.common.exceptions.NoSuchElementException:
        return None
    flag = False
    adjectives = []
    wait_for_element_to_load(driver, By.TAG_NAME, 'tr')
    table_names = table.find_elements_by_tag_name('tr')
    for table_name in table_names:
        wait_for_element_to_load(driver, By.CSS_SELECTOR, '.gt-baf-cell.gt-baf-pos-head')
        if table_name.find_elements_by_css_selector('.gt-baf-cell.gt-baf-pos-head') and 'имя прилагательное' in table_name.text:
            flag = True
            continue
        elif table_name.find_elements_by_css_selector('.gt-baf-cell.gt-baf-pos-head') and 'имя прилагательное' not in table_name.text:
            flag = False
            continue
        if flag:
            try:
                wait_for_element_to_load(driver, By.CLASS_NAME, 'gt-baf-word-clickable')
                adjectives.append(table_name.find_element_by_class_name('gt-baf-word-clickable').text)
            except selenium.common.exceptions.NoSuchElementException:
                continue

    print(adjectives)
    true_adjectives = []
    counter = 0
    for adjective in adjectives:
        query = 'https://translate.google.ru/?#' + '/'.join([target_language, source_language, adjective])
        driver.get(query)
        wait_for_element_to_load(driver, By.XPATH, '//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[3]/span[2]')
        try:
            driver.find_element_by_xpath('//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[3]/span[2]').click()
        except (selenium.common.exceptions.ElementNotVisibleException, selenium.common.exceptions.WebDriverException):
            pass
        wait_for_element_to_load(driver, By.XPATH, '//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[2]/table')
        table = driver.find_element_by_xpath('//*[@id="gt-lc"]/div[2]/div[2]/div/div/div[2]/table')
        flag = False
        wait_for_element_to_load(driver, By.TAG_NAME, 'tr')
        try:
            table_names = table.find_elements_by_tag_name('tr')
        except selenium.common.exceptions.StaleElementReferenceException:
            continue
        for table_name in table_names:
            wait_for_element_to_load(driver, By.CSS_SELECTOR, '.gt-baf-cell.gt-baf-pos-head')
            try:
                if table_name.find_elements_by_css_selector(
                        '.gt-baf-cell.gt-baf-pos-head') and 'имя прилагательное' in table_name.text:
                    flag = True
                    continue
                elif table_name.find_elements_by_css_selector(
                        '.gt-baf-cell.gt-baf-pos-head') and 'имя прилагательное' not in table_name.text:
                    flag = False
                    break
                if flag:
                    counter +=1
                    wait_for_element_to_load(driver, By.CLASS_NAME, 'gt-baf-word-clickable')
                    print(to_translate, table_name.find_element_by_class_name('gt-baf-word-clickable').text.lower())
                    if to_translate.lower() == table_name.find_element_by_class_name('gt-baf-word-clickable').text.lower():
                        true_adjectives.append(adjective)
                    if counter >=5:
                        break
            except (selenium.common.exceptions.NoSuchElementException, selenium.common.exceptions.StaleElementReferenceException):
                continue
    driver.close()
    print(true_adjectives)
    return true_adjectives


def google_translate_single(to_translate, source_language, target_language, reverse=False):
    """
    Обёртка гуглового апи
    :param to_translate:
    :param source_language:
    :param target_language:
    :param reverse:
    :return:
    """
    if reverse:
        source_language, target_language = target_language, source_language
    google_credentials = google.oauth2.service_account.Credentials.from_service_account_file(conf.PATH_TO_OAUTH2)
    translator = google.cloud.translate.Client(credentials=google_credentials)
    translation_data = (translator.translate(values=to_translate, source_language=source_language, target_language=target_language))
    return translation_data[GOOGLE_TRANSLATION_ATTR]


def yandex_translate_single(to_translate, source_language, target_language, reverse=False):
    """
    Обёртка яндексового апи
    :param to_translate:
    :param source_language:
    :param target_language:
    :param reverse:
    :return:
    """
    if reverse:
        source_language, target_language = target_language, source_language
    language_direction = f"{source_language}-{target_language}"
    translate_params = {'key': conf.YANDEX_API_KEY,
                        'text': to_translate,
                        'lang': language_direction}
    translate_request = requests.get(YANDEX_TRANSLATE_REQUEST, translate_params)
    translation_data = json.loads(translate_request.text)
    print(translation_data, to_translate)
    translation_vars = translation_data[YANDEX_TRANSLATION_ATTR]
    return translation_vars[0]


# TODO: abbyy translate parsing

# def abbyy_translate(values, source_language_number, target_language_number):
#     authorization = requests.post(definitions.ABBYY_AUTH_REQUEST, headers=conf.ABBYY_AUTH_HEADER)
#     headers = {'Authorization': f'Bearer {authorization.text}'}
#     for elem in values:
#         translate_params = {'text': elem,
#                             'srcLang': source_language_number,
#                             'dstLang': target_language_number}
#         translate_request = requests.get(definitions.ABBYY_TRANSLATE_REQUEST, params=translate_params, headers=headers)
#         raw_data = json.loads(translate_request.text, encoding='utf-8')
# #        print(json.dumps(raw_data, indent=4, sort_keys=True, ensure_ascii=False))
#         for elem in raw_data:
#             print(elem['Dictionary'])
#             print()
#             print()
#             for elem1 in elem['Body']:
#                 try:
#                     if elem1['Type'] == 3:
#                         for item in elem1['Items']:
#                             print(item)
#                         print()
#                 except KeyError:
#                     print(elem1)
#                     pass
#                 print()


if __name__ == '__main__':
    pass