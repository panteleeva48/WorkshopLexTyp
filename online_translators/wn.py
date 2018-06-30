import json
import nltk
from nltk.corpus import wordnet as wn
from nltk import download
from nltk.corpus import webtext, brown
from nltk.probability import FreqDist
import pickle
import pandas as pd



download('brown')


with open('cache\\noun_translations.json', 'r', encoding='utf-8') as dump_file:
    translations = json.load(dump_file)


for field in translations:
    src = {}
    idx = 0
    ft = translations[field]
    dirs = [dir for dir in ft if dir.startswith('en')]
    english_goldens = []
    for dir in dirs:
        english_goldens += [golden['source'] for golden in ft[dir]]
    for golden in english_goldens:
        src[idx] = [golden, ' ', ' ', ]
        idx += 1
        synonyms = []
        try:
            golden_synset = wn.synset('_'.join(golden.split()) + '.n.01')
        except nltk.corpus.reader.wordnet.WordNetError:
            continue
        synsets = (wn.synsets('_'.join(golden.split()), pos=wn.NOUN))
        lemmas = [synset.lemmas() for synset in synsets]
        words = []
        for lemma in lemmas:
            words += [word.name() for word in lemma]
        words = set(words)
        for word in words:
            word_synset = wn.synset(word + '.n.01')
            if wn.wup_similarity(golden_synset, word_synset) > 0.5:
                src[idx] = [' ', word, wn.wup_similarity(golden_synset, word_synset)]
                idx +=1
    pd.DataFrame.from_dict(src, orient='index', columns=['source_word', 'synonym', 'similarity']).to_excel('synonyms\\' + field + '_noun_synonyms.xlsx')