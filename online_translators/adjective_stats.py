import matplotlib.pyplot
import json
import os


matplotlib.pyplot.style.use('ggplot')


def count_all_accuracy(translations, goldens):
    accuracies = {}
    print(translations)
    for filename, translation in translations.items():
        field, language_1, language_2 = os.path.splitext(filename)[0].split('_')
        for golden_filename, golden_file in goldens.items():
            if golden_filename in filename:
                accuracy = len(set(translation) & set(golden_file)) / len(golden_file)
                accuracies.setdefault(field, {}).setdefault(language_1, {})[language_2] = accuracy
                break
    return accuracies

from definitions import NLTK_LANGUAGE_TAG_MAPPER, TRANSLATORS

remap = {'yandex_translate_single' : "Yandex translator", 'google_translate_single' : 'Google translator'}
import pandas

import pandas.plotting
def create_table(accuracies):
    headers = accuracies.keys()
    df_sources = {}
    for field, field_accuracy in accuracies.items():
        for source_language, direction_accuracy in field_accuracy.items():
            index = direction_accuracy.keys()
            print(index)
            for itermediate_language, inter_accuracy in direction_accuracy.items():
                df_sources.setdefault(field, {})[NLTK_LANGUAGE_TAG_MAPPER[source_language] +'_' + NLTK_LANGUAGE_TAG_MAPPER[itermediate_language]] = inter_accuracy
    print(df_sources)
    for field, df_source in df_sources.items():
        d = pandas.DataFrame.from_dict(df_source)
        print(d)
        d.to_excel('xlsx_accuracy\\' + field + '_translation_adjective.xlsx')

def plot_all_accuracy(accuracies):
    for field, directions in accuracies.items():
        y_s = {}
        fig, ax = matplotlib.pyplot.subplots(figsize=(7, 10))
        x_labels = []
        for direction, translators in directions.items():
            for translator, accuracy in translators.items():
                y_s.setdefault(translator, []).append(accuracy)
            label = NLTK_LANGUAGE_TAG_MAPPER[direction.split('_')[0]]+ ' to ' +NLTK_LANGUAGE_TAG_MAPPER[direction.split('_')[-1]]
            x_labels.append(label)
        plots = []
        for translator, x in y_s.items():
            plots.append(ax.plot(x, label=remap[translator]))
        matplotlib.pyplot.xticks(range(len(x_labels)), x_labels, rotation=30)
        ax.legend()
        matplotlib.pyplot.ylabel('Accuracy')
        matplotlib.pyplot.xlabel('Translation direction')
        matplotlib.pyplot.title('Noun translation, "' + field.capitalize() + '" field')
        matplotlib.pyplot.savefig('pics\\' + field + '_adjective_stats.png')

if __name__ == '__main__':
    with open('cache\\adj_translations.json', 'r', encoding='utf-8') as dump_file:
        translations = json.load(dump_file)
    with open('cache\\goldens.json', 'r', encoding='utf-8') as dump_file:
        goldens = json.load(dump_file)
    acc = count_all_accuracy(translations, goldens)
    print(acc)
    #plot_all_accuracy(acc)
    create_table(acc)
