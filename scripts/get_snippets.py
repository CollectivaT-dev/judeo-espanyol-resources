import requests
import os
import re
import Levenshtein as lv
from bs4 import BeautifulSoup as bs4

PATH = os.path.dirname(os.path.realpath(__file__))

def main():
    url = "https://sefarad.com.tr/judeo-espanyolladino/frazadeldia/"
    res = requests.get(url)
    soup = bs4(res.content, 'html.parser')

    audios = []
    for element in soup.findAll('audio'):
        source = element.get('src')
        if source:
            audios.append(source)

    imgs = []
    for img in soup.findAll('img'):
        if img.get('srcset'):
            img_list = [i.split() for i in img.get('srcset').split(',')]
            for im in img_list:
                im[1] = int(im[1].replace('w',''))
            img_list.sort(key = lambda i:i[1], reverse=True)
            # TODO check if image exists
            imgs.append(img_list[0][0])

    write(audios, 'audios.ls')
    write(imgs, 'imgs.ls')

    audio_img = align(audios, imgs)
    get_rest(audios, imgs, audio_img)
    print('audio not found for the following:')
    print(imgs)
    write(['%s,%s'%(ai[0],ai[1]) for ai in audio_img], 'audio_img.csv')

def write(ls, filename):
    filepath = os.path.join(PATH, '../resources', filename)
    with open(filepath, 'w') as out:
        for element in ls:
            out.write('%s\n'%element)

def align(audios, imgs):
    audio_img = []
    for audio in audios:
        for i, img in enumerate(imgs):
            if compare(audio, img) > 0.65:
                audio_img.append((audio, img))
                imgs.pop(i)
                break
    return audio_img

def compare(audio, img):
    return lv.ratio(clean(audio), clean(img))

def clean(string):
    return os.path.basename(string).replace('.ogg','').replace('.jpeg','').lower()

def get_rest(audios, imgs, audio_img):
    audios_matched = [a[0] for a in audio_img]
    audios_left = list(set(audios).difference(set(audios_matched)))
    for audio in audios_left:
        a_no = int(re.search('^\d+', clean(audio)).group())
        for i, img in enumerate(imgs):
            i_no = int(re.search('^\d+', clean(img)).group())
            if a_no == i_no:
                audio_img.append((audio, img))
                imgs.pop(i)
                break

if __name__ == "__main__":
    main()
