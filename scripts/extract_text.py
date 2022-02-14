import os
import re

PATH = os.path.dirname(os.path.realpath(__file__))
RE_JE = re.compile('(?<=(FRASE AL DIA\s\s))(.|\s)*?(?=\s\s)')

results = []
non_results = []
txt_path = os.path.join(PATH,'../txts_full')
ref_path = os.path.join(PATH, '../resources/', 'audio_img.csv')
ai = [line.strip().split(',') for line in open(ref_path).readlines()]
ai_dict = {os.path.basename(i): os.path.basename(a) for a,i in ai}
for f in os.listdir(txt_path):
    if f.endswith('txt') and not re.search('300', f):
        s = open(os.path.join(txt_path,f)).read()
        s = re.sub('(TR|JUDEO)', '\n', s)
        s = s.replace('DiA', 'DIA')
        m = RE_JE.search(s)
        if not m:
            print(f)
            print(s)
            non_results.append(f)
        else:
            je_text = m.group()
            je_text = je_text.replace('\n', ' ').replace('"','')
            if je_text:
                results.append((f, je_text))
            else:
                non_results.append(f)

with open(os.path.join(PATH, '../resources/transcripts.csv'), 'w') as out:
    for r in results:
        image = r[0].replace('_cl.txt','.jpeg')
        out.write('%s,%s,"%s"\n'%(image, ai_dict[image], r[1]))
    for r in non_results:
        image = r.replace('_cl.txt','.jpeg')
        out.write('%s,%s,""\n'%(image, ai_dict[image]))
