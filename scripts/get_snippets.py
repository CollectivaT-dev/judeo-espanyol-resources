import requests
import os
import re
import Levenshtein as lv
import subprocess
from bs4 import BeautifulSoup as bs4
from math import ceil

PATH = os.path.dirname(os.path.realpath(__file__))

def main():
    #scrape()
    download_merge()

def scrape():
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

def download_merge():
    filepath = os.path.join(PATH, '../resources/', 'audio_img.csv')
    ai = [line.strip().split(',') for line in open(filepath).readlines()]
    create_dir('audio')
    create_dir('image')
    create_dir('video')
    for audio, image in ai:
        audio_path = save('audio', audio)
        image_path = save('image', image)
        print(audio, image)
        print('** merging')
        merge_base(audio_path, image_path, 'video')

def create_dir(name):
    if not os.path.exists(name):
        os.mkdir(name)

def save(path, url):
    filepath = os.path.join(path, os.path.basename(url))
    if not os.path.isfile(filepath):
        r = requests.get(url)
        with open(filepath, 'wb') as f:
            f.write(r.content)
    else:
        print('skipping %s'%filepath)
    return filepath

def merge_base(audio, image, path, overwrite=False):
    video_path = os.path.join(path, os.path.basename(audio))[:-3]+'mp4'
    if not os.path.isfile(video_path) or not overwrite:
        # merge
        length = int(ceil(get_audio_length(audio))+2)
        args = ['ffmpeg', '-y', '-r', '1/%i'%length, '-i', image, '-i', audio,
                '-vf', 'fps=25,format=yuv420p', video_path]
        print(' '.join(args))
        process = subprocess.Popen(args,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        stdout, stderr = process.communicate()
        print(stdout)
        print(stderr.decode())
        # add fadein
        # add fadeout
    else:
        print('skipping merge')

def get_audio_length(audio):
    return 4.1

if __name__ == "__main__":
    main()
