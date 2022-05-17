# Judeo-Espanyol resources

Scripts, resources and other tools to create datasets for the Judeo-Espanyol (Ladino) language.

## Audio conversion and cleaning

This part of the process is not in the scripts, and launched from the shell.

```
for f in audio/*.ogg; do t=${f%.ogg}.wav; echo ffmpeg -i $f -ar 22050 $t -v error; done;
mv audio/*.wav dataset_wav/
for f in dataset_wav/*.wav;do t=${f##*/}; sox $f dataset_sil/$t silence 1 0.02 0.1% reverse silence 1 0.02 0.1% reverse; done
for f in dataset_sil/*.wav;do t=${f##*/}; sox $f dataset_sil_pad/$t pad 0 0.058; done
```

In order to introduce the data into Coqui TTS, the transcript file has to be prepared. After the edition of the `transcripts_edited.csv` is finished:

```
awk -F'\t' '{print $2"\t"$3,$3}' resources/transcripts_edited.csv | sed 's/\.ogg/\.wav/g; s|^|fraza_dataset/wav/|g; s/\t/|/g' > fraza_dataset/transcripts.txt
```
## Salom newspaper scraping scripts

IPython notebooks for scraping ladino articles from [Salom newspaper](https://www.salom.com.tr/) are provided in [notebooks/scraping.ipynb](https://github.com/CollectivaT-dev/judeo-espanyol-resources/blob/main/notebooks/scraping.ipynb)
