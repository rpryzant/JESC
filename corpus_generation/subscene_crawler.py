"""
=== DESCRIPTION
This is a crawler for subscene.com. 

=== INPUTS
A text file with one subtitle url per line, e.g.: 

```
https://subscene.com/subtitles/win-who-is-next--mnet-reality-show/japanese/1478919
https://subscene.com/subtitles/hwarang-the-poet-warrior-youth/japanese/1478121
https://subscene.com/subtitles/seven-first-kisses/japanese/1478085
https://subscene.com/subtitles/romantic-doctor-teacher-kim/japanese/1477487
https://subscene.com/subtitles/romantic-doctor-teacher-kim/japanese/1477447
```

=== OUTPUTS:
root/   (this is your [base dir] argument)                                                                                          
    title_i/
       en/
         .srt files
    ... 

=== USAGE
python crawler.py [url file] [base dir]




"""
# coding: utf-8

import sys
from selenium import webdriver
import os
import uuid
import magic
from pyunpack import Archive
from ffmpy import FFmpeg
import re
import shutil
from joblib import Parallel, delayed
from tqdm import tqdm

def file_length(f):
    """ gets the length of a file
    """
    return int(os.popen('wc -l %s' % f).read().strip().split()[0])


def download_subfile(url, name, dest):
    """ download a subscene file at url "url" to 
        the location specified by "dest"
    """
    def get_dl_button(url):
        try:
            driver.get(url)
            return driver.find_element_by_id('downloadButton')
        except:
            print 'ERROR: cant get dl button ', url
            return False
            
    if not os.path.exists(dest):
        os.makedirs(dest)

    # download file
    elem = get_dl_button(url)
    if not elem:
        elem = get_dl_button(url)
    if not elem:
        print 'ERROR: couldnt get dl button x2', url
        return None
            
    dl_link = elem.get_attribute('href')
    dl_id = str(uuid.uuid4())
    target = os.path.join(dest, name + '-' + dl_id)
    os.system('wget -nc -P %s %s -O %s' % (dest, dl_link, target))

    return target


def convert_all_to_srt(dir):
    """ converts all the files in a dir to srt format
    """
    def convert_to_srt(target, dest):
        ff = FFmpeg(
            inputs={target: None},
            outputs={dest: None})
        ff.run()

    for f in os.listdir(dir):
        try:
            f = os.path.join(dir, f)
            if '.srt' not in f:
                convert_to_srt(f, f + '.srt')
        except:
            print 'ERROR: CONVERSION FAILURE ON', f


def extract_archive(target, dest):
    """ tries to extract an archive
    """
    try:
        Archive(target).extractall(dest)
    except:
        pass

def rm_exclude(dir, suffix):
    os.system("find %s -type f ! -name '*%s' -delete" % (dir, suffix))


def dl_and_convert(dest, url, title):
    """ downloads a file from url "url" into destination "dest",
            and then converts it to srt format
    """
    dlded_filepath = download_subfile(url, title, dest)
    if dlded_filepath:
        output = extract_archive(dlded_filepath, dest)
        convert_all_to_srt(dest)
        rm_exclude(dest, '.srt')
        return True
    else:
        return False


def should_skip(base_dir, title, language):
    """ a title should be skipped if it's english AND one of the 
        following cases holds:
             - there's not ja subs for the title
             - if the title is already done

    """
    if language == 'en':
        # skip if there's no ja subs for this title
        if not os.path.exists(os.path.join(base_dir, title)):
            return True

        # skip if this title is already done
        else:
            en_sub_dir = os.path.join(base_dir, title, 'en')
            en_subs = os.listdir(en_sub_dir)
            if any(map(lambda x: 'srt' in x, en_subs)):
                return True
        return False


url_base = lambda url: re.findall("https://subscene.com/subtitles/(.*)/[japanese|english]", url)[0]
base_dir = sys.argv[2]

def process_url(url, language):
    try:
        title = url_base(url)
        if should_skip(base_dir, title, language):
            print 'SKIPPED ', url
            return

        dest = os.path.join(base_dir, title, language)
        if dl_and_convert(dest, url, title):
            print 'SUCCESS ON', url
        else:
            print 'FAILURE ON ', url
    except Exception as e:
        print 'MYSTERIOUS FAILURE ON: ', url, ' WITH EXCEPTION ', e


urls = sys.argv[1]
url_f = open(urls)
language = 'ja' if 'ja' in urls else 'en'
url_base = lambda url: re.findall("https://subscene.com/subtitles/(.*)/[japanese|english]", url)[0]
driver = webdriver.Chrome()
driver.set_page_load_timeout(10)   # 10 second limit 


for i, url in tqdm(enumerate(url_f), total=file_length(sys.argv[1])):
    process_url(url, language)

#Parallel(n_jobs=4)(delayed(process_url)(url) for url in ja_urls)





