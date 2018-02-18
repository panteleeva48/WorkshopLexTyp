#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xlrd
import csv
import os
import re
import nltk.corpus
import nltk.stem.snowball
from definitions import NLTK_LANGUAGE_TAG_MAPPER, MATCH_ALL_EXCEPT_UNICODE_LETTERS
import translate
import copy
import json


LANGUAGES = ['ru', 'de', 'fr', 'en', 'it']
GOOD_LANGS = ['en', 'ru']


def filter_stops(to_filter, raw_language_code):
    _nltk_language_code = NLTK_LANGUAGE_TAG_MAPPER[raw_language_code]
    _stopwords = nltk.corpus.stopwords.words(_nltk_language_code)
    return [word for word in to_filter if word not in _stopwords]


def make_lowercase_and_clean(word):
    """
    Убираем все кроме маленьких букв (оставляя пробелы) из строки
    :param word:
    :return:
    """
    lowercase_word = word.lower()
    cleaned_word = re.sub(MATCH_ALL_EXCEPT_UNICODE_LETTERS, '', lowercase_word)
    no_spaces_cleaned_word = cleaned_word.rstrip()
    return no_spaces_cleaned_word


class AdjectiveQuestionnaireParser:

    def __init__(self, filename):
        self.filename = filename
        self.adjectives = None
        self.raw_questionnaire = None
        self.gold_standard = None
        self._get_info()
        self._get_questionnaire()
        print(filename, self.adjectives)




    def __str__(self):
        return self.filename

    __repr__ = __str__

    def _get_questionnaire(self):
        with open(self.filename,
                  mode='r', newline='', encoding='utf-8') as _questionnaire_csv:
            _questionnaire_csv_reader = csv.reader(_questionnaire_csv, delimiter=',')
            self.adjectives = list(filter(None, next(_questionnaire_csv_reader)))

    def _get_info(self):
        name_without_extension = os.path.splitext(self.filename)[0]
        _filename_split = name_without_extension.split('\\')[-1].split('_')
        self.language = _filename_split.pop()
        self.field = _filename_split.pop()



def extract_noun_csv_sheets(excel_file):
    workbook = xlrd.open_workbook(excel_file)
    all_worksheets = workbook.sheet_names()
    for worksheet_name in all_worksheets:
        if worksheet_name.startswith('adj'):
            worksheet = workbook.sheet_by_name(worksheet_name)
            questionnaire_typename = excel_file.split('\\')[1].split('_')[1]
            csv_name = questionnaire_typename + '_' + worksheet_name.split('_')[-1]
            with open('questionnaire_csvs\\' + csv_name + '.csv', 'wt', encoding='utf-8') as your_csv_file:
                csv_writer = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)
                for rownum in range(worksheet.nrows):
                    csv_writer.writerow([entry for entry in worksheet.row_values(rownum)])


def extract_adjective_csv_sheets_directory(directory_name):
    for root, dirs, filenames in os.walk(directory_name):
        for filename in filenames:
            current_path = os.path.join(root, filename)
            extract_noun_csv_sheets(current_path)


def parse_csv_questionnaires(directory_name):
    questionnaires = []
    for root, dirs, filenames in os.walk(directory_name):
        for filename in filenames:
            current_path = os.path.join(root, filename)
            current_questionnaire = AdjectiveQuestionnaireParser(current_path)
            questionnaires.append(current_questionnaire)
    return questionnaires


class Compil:

    def __init__(self, questionnaires):
        self.golden_standards = questionnaires
        self.good_questionnaires = []
        self.translations = {}
        self._get_translations()



    def _get_translations(self):
        for source_questionnaire in self.golden_standards:
            curr_questionnaires = copy.copy(self.golden_standards)
            curr_questionnaires.remove(source_questionnaire)
            for target_questionnaire in curr_questionnaires:
                if source_questionnaire.field == target_questionnaire.field:
                    translated_adjectives = []
                    try:
                        for adjective in source_questionnaire.adjectives:
                                translated_adjectives += translate.google_synonym_tranlate(adjective, source_language=source_questionnaire.language, target_language=target_questionnaire.language)
                    except TimeoutError:
                        continue
                    direction = target_questionnaire.field +'_'+ target_questionnaire.language +'_'+ source_questionnaire.language
                    self.translations[direction] = translated_adjectives
        with open('cache\\adj_translations.json', 'w', encoding='utf-8') as output_file:
            json.dump(self.translations, output_file)
        goldens = {}
        for questionnaire in self.golden_standards:
            goldens[os.path.splitext(questionnaire.filename.split('\\')[-1])[0]] = questionnaire.adjectives
        with open('cache\\goldens.json', 'w', encoding='utf-8') as output_file:
            json.dump(goldens, output_file, ensure_ascii=False)

    def process_word(self, word, language, stemmer):
        clean_translation = make_lowercase_and_clean(word)
        split_translation = clean_translation.split()
        filtered_translations = filter_stops(split_translation, language)
        stemmed_translation = [stemmer.stem(filtered_translation) for filtered_translation in
                               filtered_translations]
        return stemmed_translation


from definitions import RAW_DATA_PATH


def get_all_questionnaire_translations():
    extract_adjective_csv_sheets_directory(RAW_DATA_PATH)
    questionnaires = parse_csv_questionnaires('questionnaire_csvs')
    results = {}
    Compil(questionnaires)


if __name__ == '__main__':
    get_all_questionnaire_translations()