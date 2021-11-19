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
    #TODO parametrize dir names to propagate later
    create_dir('audio')
    create_dir('image')
    create_dir('video')
    for audio, image in ai:
        audio_path = save('audio', audio)
        image_path = save('image', image)
        image_path = fix_image(image_path)
        print(audio, image)
        print('** merging')
        video_path = merge_base(audio_path, image_path, 'video', w_fadein=False)
        merge_intro_outro(video_path, w_intro=False)

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

def fix_image(path):
    patch_path = os.path.join(PATH, '../assets/', 'patch.jpeg')
    new_path = path.replace('.jpeg', '_cl.jpeg')
    args = ['composite',  '-geometry', '+0+0', patch_path, path, new_path]
    stdout, stderr = run(args)
    return new_path

def merge_base(audio, image, path, overwrite=False, w_fadein=True):
    if w_fadein:
        extension = '.mp4'
    else:
        extension = '_f.mp4'
    video_path = os.path.join(path, os.path.basename(audio))[:-4]+extension
    print(video_path)
    if not os.path.isfile(video_path) and not overwrite:
        # merge
        length = int(ceil(get_audio_length(audio))+2)
        args = ['ffmpeg', '-y', '-r', '1/%i'%length, '-i', image, '-i', audio,
                '-vf', 'fps=25,format=yuv420p', 'dummy.mp4']
        run(args)
        # parameters for the case wo_fadein, which are overwritten if w_fadein
        infile = 'dummy.mp4'
        if w_fadein:
            outfile = 'dummy2.mp4'
            # add fadein
            args = ['ffmpeg', '-y', '-i', infile, '-vf', 'fade=t=in:st=0:d=1.5',
                    '-c:a', 'copy', outfile]
            run(args)
            infile = 'dummy2.mp4'
        # add fadeout
        fadeout_start = length - 0.5
        args = ['ffmpeg', '-y', '-i', infile, '-vf',
                'fade=t=out:st=%2.1f:d=0.5'%fadeout_start,
                '-c:a', 'copy', video_path]
        run(args)
    else:
        print('skipping merge')
    return video_path

def run(args):
    print(' '.join(args))
    process = subprocess.Popen(args, stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout, stderr

def get_audio_length(audio):
    args = 'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1'.split()+[audio]
    process = subprocess.Popen(args, stdout = subprocess.PIPE,
                                     stderr = subprocess.PIPE)
    stdout, stderr = process.communicate()
    duration = stdout.decode()
    print(duration)
    return float(duration)

def merge_intro_outro(video_path, overwrite=False, w_intro=True):
    intro_path = os.path.join(PATH, '../assets', 'intro.mp4')
    if w_intro:
        extension = '_io.mp4'
    else:
        extension = '_o.mp4'
    video_io_path = video_path.replace('.mp4', extension)
    if not os.path.isfile(video_io_path) and not overwrite:
        # this is case wo_intro that is overwritten in w_intro = True
        infile = video_path
        if w_intro:
            outfile = 'dummy3.mp4'
            args = ['ffmpeg', '-y', '-i', intro_path, '-i', infile, '-f', 'lavfi',
                    '-t', '1', '-i', 'anullsrc', '-filter_complex',
                    '[0:v][2:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]',
                    '-map', "[v]", '-map', "[a]", outfile]
            stdout, stderr = run(args)
            infile = 'dummy3.mp4'
        args = ['ffmpeg', '-y', '-i', infile, '-i', intro_path, '-f', 'lavfi',
                '-t', '1', '-i', 'anullsrc', '-filter_complex',
                '[0:v][0:a][1:v][2:a]concat=n=2:v=1:a=1[v][a]',
                '-map', "[v]", '-map', "[a]", video_io_path]
        stdout, stderr = run(args)

if __name__ == "__main__":
    main()
