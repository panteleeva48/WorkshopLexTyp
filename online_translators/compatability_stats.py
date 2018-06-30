import matplotlib.pyplot
from definitions import NLTK_LANGUAGE_TAG_MAPPER
import pandas


matplotlib.pyplot.style.use('ggplot')

import os

def plot_all_accuracy(directory):
    accs = {}
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            try:
                df = pandas.read_pickle(root+filename)
                language_1, language_2, translator,  *other, field = os.path.splitext(filename)[0].split('_')
                df_golden = pandas.read_pickle('compatibility_goldens_cache\\' +language_1+'_'+field+ '_golden_df.pkl')
                df.index.name = ''
                idx = df_golden.index.difference(df.index)
                df_golden.drop(idx, inplace=True)
                cols = df_golden.columns.tolist()
                cols.sort()
                acc_curr = (df_golden[cols] & df[cols]).sum().sum()/df_golden.sum().sum()
                print((df_golden[cols] == df[cols]).sum().sum(), df_golden.sum().sum())
                accs.setdefault(field, {}).setdefault(language_1, {}).setdefault(translator, {})[language_2] = acc_curr
            except KeyError:
                continue
    print(accs)
    for field, trans_acc in accs.items():

        for source_language, language_acc in trans_acc.items():
            fig, ax = matplotlib.pyplot.subplots(figsize=(7, 10))
            for translator, dir_acc in language_acc.items():

                x = list(dir_acc.values())
                labels = []
                for language_name in dir_acc.keys():
                    labels.append(NLTK_LANGUAGE_TAG_MAPPER[language_name])
                ax.plot(x, label=translator)
            ax.legend()
            matplotlib.pyplot.xticks(range(len(labels)), labels, rotation=30)
            matplotlib.pyplot.xlabel('Intermediary language')
            matplotlib.pyplot.ylabel('Accuracy')
            matplotlib.pyplot.savefig('pics\\' + source_language + '_' + field + '_compatibility_stats.png')
    df_src = {}
    for field, trans_acc in accs.items():
        for source_language, language_acc in trans_acc.items():
            for translator, dir_acc in language_acc.items():
                df_src.setdefault(translator, {}).setdefault(field, {})[source_language] = dir_acc
    for translator, trans_acc in df_src.items():
        for field, field_acc in trans_acc.items():
            d = pandas.DataFrame.from_dict(field_acc)
            d.index.name = 'inter_language'
            d.columns.name = 'source_language'
            d.to_excel('xlsx_accuracy\\' + translator + '_' + field + '_compatibility.xlsx')


if __name__ == '__main__':
    # translations = nouns.get_all_questionnaire_translations()
    # with open('translations.json', 'w', encoding='utf-8') as dump_file:
    #     json.dump(translations.field_translation, dump_file, ensure_ascii=False)
    acc = plot_all_accuracy('compatibility_translations_cache\\')
    #plot_all_accuracy(acc)