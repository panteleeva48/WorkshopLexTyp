import matplotlib.pyplot
import nouns
import json
import collections


matplotlib.pyplot.style.use('ggplot')


def count_all_accuracy(translations):
    accuracies = {}
    errors = {}
    for field in translations.keys():
        accuracies[field] = {}
        errors[field] = {}
        field_accuracy = accuracies[field]
        for direction in translations[field].keys():
            errors[field][direction] = []
            field_accuracy[direction] = collections.defaultdict(float)
            direction_accuracy = field_accuracy[direction]
            for word_entry in translations[field][direction]:
                golden = word_entry.pop('golden')
                source = word_entry.pop('source')
                error = {}
                for translator in word_entry.keys():
                    if set(word_entry[translator]) == set(golden):
                        direction_accuracy[translator] += 1/len(translations[field][direction])
                    else:
                        error['golden'] = golden
                        error['source'] = source
                        error[translator] = word_entry[translator]
                if error:
                    errors[field][direction].append(error)
    return accuracies

from definitions import NLTK_LANGUAGE_TAG_MAPPER, TRANSLATORS

remap = {'yandex_translate_single' : "Yandex translator", 'google_translate_single' : 'Google translator'}
import pandas

import pandas.plotting
def create_table(accuracies):
    headers = accuracies.keys()
    df_sources = {}
    for field, field_accuracy in accuracies.items():
        for direction, direction_accuracy in field_accuracy.items():
            index = direction_accuracy.keys()
            for translator, translator_accuracy in direction_accuracy.items():
                print(index)
                df_sources.setdefault(field, {}).setdefault(direction, {})[remap[translator]] = translator_accuracy
    print(df_sources)
    for field, df_source in df_sources.items():
        d = pandas.DataFrame.from_dict(df_source)
        d.to_excel('xlsx_accuracy\\' + field + '_translation_noun.xlsx')

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
        matplotlib.pyplot.savefig(field + '_noun_stats.png')

if __name__ == '__main__':
    translations = nouns.get_all_questionnaire_translations()
    with open('cache\\noun_translations.json', 'w', encoding='utf-8') as dump_file:
        json.dump(translations.field_translation, dump_file, ensure_ascii=False)
    with open('cache\\noun_translations.json', 'r', encoding='utf-8') as dump_file:
        translations = json.load(dump_file)
    acc = count_all_accuracy(translations)
    #plot_all_accuracy(acc)
    create_table(acc)
