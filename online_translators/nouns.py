#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xlrd
import csv
import os
import re
import nltk.corpus
import itertools
from definitions import NLTK_LANGUAGE_TAG_MAPPER, QUESTIONNAIRE_PATH, TRANSLATORS, MATCH_ALL_EXCEPT_UNICODE_LETTERS, \
    RAW_DATA_PATH



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


class NounQuestionnaireParser:

    def __init__(self, filename, reverse=False):
        self.filename = filename
        self.name_without_extension = None
        self.language_1 = None
        self.language_2 = None
        self.raw_questionnaire = None
        self.gold_standard = {}
        # self.translation_results = {}
        # self.reverse_translation_results = {}
        self._get_info()
        # if reverse:
        #     self.language_1, self.language_2 = self.language_2, self.language_1
        #     self.gold_standard = {target_word: source_word for source_word, target_word in self.gold_standard.items()}
        self._get_questionnaire()
        self._get_gold_standard()
        # self._get_translation_results()

    def _get_questionnaire(self):
        print(self.filename)
        with open(self.filename,
                  mode='r', newline='', encoding='utf-8') as _questionnaire_csv:
            _questionnaire_csv_reader = csv.reader(_questionnaire_csv, delimiter=',')
            next(_questionnaire_csv_reader, None)
            self.raw_questionnaire = list(filter(None, list(_questionnaire_csv_reader)))

    def _get_info(self):
        self.name_without_extension = os.path.splitext(self.filename)[0]
        _filename_split = self.name_without_extension.split('\\')[-1].split('_')
        self.language_2 = _filename_split.pop()
        self.language_1 = _filename_split.pop()
        self.field = _filename_split.pop()

    def _get_gold_standard(self):
        with_adj = True
        count = 0
        for _questionnaire_entry in self.raw_questionnaire:
            if len(_questionnaire_entry[0].split()) == 1:
                count +=1
        if count > len(self.raw_questionnaire)/10:
            with_adj = False
        for _questionnaire_entry in self.raw_questionnaire:
            _target_language_word = make_lowercase_and_clean(_questionnaire_entry[1])
            if _target_language_word != '':  # Бывают строки анкет другого формата, где нет перевода русского конекста
                if with_adj:
                    new_word = ' '.join(_questionnaire_entry[0].split()[1:])
                else:
                    new_word = _questionnaire_entry[0]
                _source_language_word = make_lowercase_and_clean(new_word)  # В другом формате русские эквиваленты
                #  употребляются вместе с прилагательными, но стандартно в конце словосочетания
                if _source_language_word:
                    self.gold_standard[_source_language_word] = _target_language_word
                else:
                    continue
        print(self.gold_standard)



def extract_noun_csv_sheets(excel_file):
    workbook = xlrd.open_workbook(excel_file)
    all_worksheets = workbook.sheet_names()
    for worksheet_name in all_worksheets:
        if worksheet_name.startswith('csv'):
            worksheet = workbook.sheet_by_name(worksheet_name)
            questionnaire_typename = os.path.splitext(excel_file.split('\\')[1].split('_')[1])[0]
            csv_name = questionnaire_typename + '_' + '_'.join(worksheet_name.split('_')[1:])
            with open('noun_csvs\\' + csv_name + '.csv', 'wt', encoding='utf-8') as your_csv_file:
                csv_writer = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)
                for rownum in range(worksheet.nrows):
                    csv_writer.writerow([entry for entry in worksheet.row_values(rownum)])


def extract_noun_csv_sheets_directory(directory_name):
    for root, dirs, filenames in os.walk(directory_name):
        for filename in filenames:
            current_path = os.path.join(root, filename)
            extract_noun_csv_sheets(current_path)


class GoldenStandardsCompiler:

    def __init__(self, same_type_questionnaires):
        self.raw_questionnaires = same_type_questionnaires
        self.field_gold_standards = {}
        self.compile_questionnaires_gold_standard()

    def search_word_entry(self, word, field):
        search_generator = (word_entry for word_entry in self.field_gold_standards[field] if word in word_entry.values())
        return next(search_generator, None)


    def compile_questionnaires_gold_standard(self):
        for questionnaire in self.raw_questionnaires:
            if questionnaire.field not in self.field_gold_standards.keys():
                self.field_gold_standards[questionnaire.field] = []
            for source_word, gold_translation in questionnaire.gold_standard.items():
                searched_source_word_entry = self.search_word_entry(source_word, questionnaire.field)
                searched_golden_word_entry = self.search_word_entry(gold_translation, questionnaire.field)
                if searched_source_word_entry is not None:
                    if questionnaire.language_2 not in searched_source_word_entry.keys():
                        searched_source_word_entry[questionnaire.language_2] = gold_translation
                    continue
                if searched_golden_word_entry is not None:
                    if questionnaire.language_2 not in searched_golden_word_entry.keys():
                        searched_golden_word_entry[questionnaire.language_1] = source_word
                    continue
                word_entry = {questionnaire.language_1: source_word, questionnaire.language_2: gold_translation}
                self.field_gold_standards[questionnaire.field].append(word_entry)
        print(self.field_gold_standards)


def parse_csv_questionnaires(directory_name):
    questionnaires = []
    for root, dirs, filenames in os.walk(directory_name):
        for filename in filenames:
            current_path = os.path.join(root, filename)
            current_questionnaire = NounQuestionnaireParser(current_path)
            questionnaires.append(current_questionnaire)
    return questionnaires


class GoldenStandardsTranslator:

    def __init__(self, golden_standard):
        self.golden_standards = golden_standard
        self.field_translation = {}
        self._get_translations()

    def _get_translations(self):
        for field in self.golden_standards.keys():
            self.field_translation[field] = {}
            for word_entry in self.golden_standards[field]:
                for source_language, target_language in itertools.permutations(word_entry.keys(), 2):
                    source_word = word_entry[source_language]
                    target_word = word_entry[target_language]
                    translation_type = source_language + '_' + target_language
                    translation_result = self._get_translation(source_word, source_language, target_language)
                    translation_result['source'] = source_word
                    translation_result['golden'] = filter_stops(make_lowercase_and_clean(target_word).split(), raw_language_code=target_language)
                    self.field_translation[field].setdefault(translation_type, []).append(translation_result)
        print(self.field_translation)

    def _get_translation(self, source_word, source_language, target_language):
        translation_versions = {}
        for translate_function in TRANSLATORS:
                translated_word = translate_function(source_word, source_language, target_language)
                clean_translation = make_lowercase_and_clean(translated_word)
                split_translation = clean_translation.split()
                filtered_translation = filter_stops(split_translation, target_language)
                translation_versions[translate_function.__name__] = filtered_translation
        return translation_versions


def get_translations():
    extract_noun_csv_sheets_directory(RAW_DATA_PATH)
    questionnaires = parse_csv_questionnaires(QUESTIONNAIRE_PATH)
    questionnaire_compilation = GoldenStandardsCompiler(questionnaires)
    return questionnaire_compilation.field_gold_standards


def get_all_questionnaire_translations():
    extract_noun_csv_sheets_directory(RAW_DATA_PATH)
    questionnaires = parse_csv_questionnaires(QUESTIONNAIRE_PATH)
    questionnaire_compilation = GoldenStandardsCompiler(questionnaires)
    questionnaire_translator = GoldenStandardsTranslator(questionnaire_compilation.field_gold_standards)
    return questionnaire_translator


if __name__ == '__main__':
    print(get_all_questionnaire_translations().field_translation)