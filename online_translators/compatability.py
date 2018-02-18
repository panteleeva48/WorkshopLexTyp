#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xlrd
import csv
import os
import re
import nltk.corpus
import nltk.stem.snowball
from definitions import NLTK_LANGUAGE_TAG_MAPPER, TRANSLATORS, MATCH_ALL_EXCEPT_UNICODE_LETTERS, RAW_DATA_PATH
import pandas as pd
import nouns
import google.api_core.exceptions
import google.auth.exceptions
import time
import copy


LANGUAGES = ['ru', 'de', 'fr', 'en', 'it']


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
        self.raw_questionnaire = None
        self.gold_standard = None
        self._get_info()
        self._get_questionnaire()
        self._cleanup_gold()

    def _get_questionnaire(self):
        with open(self.filename,
                  mode='r', newline='', encoding='utf-8') as _questionnaire_csv:
            _questionnaire_csv_reader = csv.reader(_questionnaire_csv, delimiter=',')
            adjectives = list(filter(None, next(_questionnaire_csv_reader)))
            nouns_compat = list(filter(None, list(_questionnaire_csv_reader)))
            new_df = pd.DataFrame(nouns_compat)
            new_df.set_index(0, inplace=True)
            new_df.columns = adjectives
        self.gold_standard = new_df

    def _cleanup_gold(self):
        for col in self.gold_standard:
            mask_true = self.gold_standard[col] != ''
            mask_false = self.gold_standard[col] == ''
            self.gold_standard.loc[mask_true, col] = True
            self.gold_standard.loc[mask_false, col] =False

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


class GoldenStandardsTest:

    def __init__(self, golden_standard, lang, field):
        self.golden_standards = golden_standard
        self.translations_src = {}
        self.lang = lang
        self.field = field
        noun_field = field
        if field == 'big' or field == 'small':
            noun_field = 'size'
        self.noun_translations = nouns.get_translations()[noun_field]
        self.index = golden_standard.index.tolist()
        self._get_translations()
        self._create_dfs()

    def _get_translations(self):
        for noun, row in self.golden_standards.iterrows():
            for adjective in row.index:
                flag = True
                for word_entry in self.noun_translations:
                    if noun.replace('ё', 'е') in word_entry.values():
                        try:
                            noun = word_entry[self.lang]
                            flag = False
                        except KeyError:
                            continue
                if flag:
                    self.index.remove(noun)
                    break
                source_phrase = adjective + ' ' + noun
                self._get_translation_src(source_phrase)


    def process_word(self, word, language, stemmer):
        clean_translation = make_lowercase_and_clean(word)
        split_translation = clean_translation.split()
        filtered_translations = filter_stops(split_translation, language)
        stemmed_translation = [stemmer.stem(filtered_translation) for filtered_translation in
                               filtered_translations]
        return stemmed_translation


    def _get_translation_src(self, source_word):
        source_stemmer = nltk.stem.snowball.SnowballStemmer(language=NLTK_LANGUAGE_TAG_MAPPER[self.lang])
        current_languages = copy.copy(LANGUAGES)
        try:
            current_languages.remove(self.lang)
        except ValueError:
            current_languages.pop()
        for target_language in current_languages:
            direction = self.lang + '_' + target_language
            for translate_function in TRANSLATORS:
                    df_name = direction + '_' + translate_function.__name__
                    colname = source_word.split()[0]
                    while True:
                        try:
                            translated_word = translate_function(source_word, self.lang, target_language)
                            retranslated_word = translate_function(translated_word, target_language, self.lang)
                            break
                        except (google.api_core.exceptions.ServiceUnavailable, google.auth.exceptions.TransportError, TimeoutError):
                            time.sleep(1)
                            continue
                    retranslated_word_processed = self.process_word(retranslated_word, self.lang, source_stemmer)
                    self.translations_src.setdefault(df_name, {}).setdefault(colname, []).append(set(retranslated_word_processed) == set(self.process_word(source_word,
                                                                                                                                                           self.lang,
                                                                                                                                                           source_stemmer)))

    def _create_dfs(self):
        self.dfs = {}
        for name in self.translations_src.keys():
            self.dfs[name] = pd.DataFrame(data=self.translations_src[name], index=self.index).to_pickle('compatibility_translations_cache\\'+name +'_'+self.field+'.pkl')


def get_all_questionnaire_translations():
    extract_adjective_csv_sheets_directory(RAW_DATA_PATH)
    questionnaires = parse_csv_questionnaires('questionnaire_csvs')
    for questionnaire in questionnaires:
        GoldenStandardsTest(questionnaire.gold_standard, questionnaire.language, questionnaire.field)
        questionnaire.gold_standard.to_pickle('compatibility_goldens_cache\\'+questionnaire.language+'_'+questionnaire.field+'_golden' + '_df.pkl')


if __name__ == '__main__':
    get_all_questionnaire_translations()
