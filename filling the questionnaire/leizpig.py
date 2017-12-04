import re

def get_sent(text):
    sentences = re.findall('\n([0-9]{1,3})(.+?)\|SENT', text, flags=re.DOTALL)
    return sentences

def get_adjnoun(text):
    adjnouns = re.findall(' ([A-Z]*)([a-z]*)\|JJ ([A-Z]*)([a-z]*)\|NN', text, flags=re.DOTALL)
    adjnoun = []
    for y in adjnouns:
        an = []
        if y[0] != '':
            adj = y[0] + y[1]
        else:
            adj = y[1]
        if y[2] != '':
            noun = y[2] + y[3]
        else:
            noun = y[3]
        an.append(adj)
        an.append(noun)
        adjnoun.append(an)
    if adjnoun != None:
        return adjnoun

file1 = open('leizpig.txt', 'r', encoding='utf-8')
text = file1.read()
file1.close()

file3 = open('test.txt', 'r', encoding='utf-8')
test = file3.read()
file3.close()
tan = re.findall(' ([a-z]+) ([a-z]+)\n', test, flags=re.DOTALL)
tans = []
for x in tan:
    ta = x[0] + '\t' + x[1]
    tans.append(ta)

file2 = open('result.csv', 'w', encoding='utf-8')
sentences = get_sent(text)
for x in range(0, len(sentences)):
    adjnoun = get_adjnoun(sentences[x][1])
    an = ''
    for i in adjnoun:
        an = i[0] + '\t' + i[1]
        for j in tans:
            if an == j:
                file2.write(an + '\n')
file2.close()
