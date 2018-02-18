import re


SOURCE_LANGUAGE = 'ru'
TARGET_LANGUAGE = 'fr'
ABBYY_SOURCE_LANGUAGE = 1049
ABBYY_TARGET_LANGUAGE = 1033
YANDEX_TRANSLATE_REQUEST = 'https://translate.yandex.net/api/v1.5/tr.json/translate?'
ABBYY_AUTH_REQUEST = 'https://developers.lingvolive.com/api/v1.1/authenticate'
ABBYY_TRANSLATE_REQUEST = 'https://developers.lingvolive.com/api/v1/Translation?'
GOOGLE_TRANSLATION_ATTR = 'translatedText'
YANDEX_TRANSLATION_ATTR = 'text'
NLTK_LANGUAGE_TAG_MAPPER = {'en': 'english', 'fr': 'french', 'it': 'italian', 'ru': 'russian', 'fin': 'finnish', 'de': 'german'}
QUESTIONNAIRE_PATH = 'noun_csvs'
MATCH_ALL_EXCEPT_UNICODE_LETTERS = re.compile(r'(?=[\W\d_])(?=[^ ]).', re.UNICODE)
GOLDEN_NAME = 'golden'
REVERSE_NAME = 'rev'
SOURCE_NAME = 'source'
TRANSLATION_PATH = 'translations'
RAW_DATA_PATH = 'raw_data'

from translate import yandex_translate_single, google_translate_single
TRANSLATORS = [
    yandex_translate_single,
    google_translate_single
]