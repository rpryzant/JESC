"""                                                                                                                                   
=== DESCRIPTION
This program takes a directory of crawled subs and produces aligned phrase pairs.

=== USAGE                                                                                                                            
python parser.py [data_loc] [en_out] [ja_out] -t [num_threads (OPTIONAL)]                                                
                                                                                                                                     
=== PRECONDITION
data_loc is structured as follows:                                                                                                     
root/   (this is your arg)                                                                                          
    title_i/
       ja/
         .srt files
       en/
         .srt files
    ... 
"""
# coding: utf-8                                                                                                                      
from joblib import Parallel, delayed
import pysrt
import sys
import numpy as np
import string
import os
import datetime
import collections
from tqdm import tqdm
import re
import string
import argparse # option parsing                                                                                                     
from guessit import guessit
from difflib import SequenceMatcher
from subfile_aligner import Aligner
import random


def process_command_line():
    """ return a tuple of args                                                                                                       
    """
    parser = argparse.ArgumentParser(description='usage')

    # positional args                                                                                                                
    parser.add_argument('data_loc', metavar='data_loc', type=str, help='crawl output directory')
    parser.add_argument('en_out', metavar='en_out', type=str, help='en output dir')
    parser.add_argument('ja_out', metavar='ja_out', type=str, help='ja output dir')
    parser.add_argument('donefile', metavar='donefile', type=str, help='file to track finished srts with')

    # optional args                                                                                                                  
    parser.add_argument('-t', '--threads', dest='num_threads', type=int, default=1, help='num threads to parse with')

    args = parser.parse_args()
    return args



def should_align(ja_f, en_f):
    """ some title-based heuristics on whether two filepaths are a match
    """
    def similarity(a, b):
        if not a or not b or len(a) == 0 or len(b) == 0:
            return 0
        return SequenceMatcher(None, a, b).ratio()

    # for testing
    def report(b):
        print b
        print ja_f
        print en_f

    ja = guessit(ja_f)
    en = guessit(en_f)


    if similarity(ja.get('title'), en.get('title')) < 0.5:
        return False

    if ja.get('type') == 'movie' and en.get('type') == 'movie':
        if similarity(ja.get('title'), en.get('title')) > 0.8 and \
           similarity(ja.get('alternative_title'), en.get('alternative_title')) > 0.9:
            return True

    if ja.get('type') == 'episode' and en.get('type') == 'episode':
        if ja.get('episode') == en.get('episode') or \
                similarity(ja.get('episode_title'), en.get('episode_title')) > 0.9:
            return True

    return False
        


def get_file_alignments(ja_subfile, en_title_root):
    """ get all the en srts that are a match for a ja srt
    
        returns: [en matches]
    """
    alignments = []
    for en_subfile in os.listdir(en_title_root):
        if should_align(ja_subfile, en_subfile):
            alignments.append(os.path.join(en_title_root, en_subfile))
    return alignments


def get_dones(donefile):
    if not os.path.exists(donefile):
        return []
    dones = open(donefile).readlines()
    dones = [x.strip() for x in dones]
    return dones


def update_dones(donefile, srt):
    with open(donefile, 'a') as dones:
        dones.write(srt + '\n')


def extract_subs(ja_srt, title_root, donefile):
    """ parse and align, and write subs for a pair of srt files
    """
    try:
        dones = get_dones(donefile)
        if ja_srt in dones:
            print 'ALREADY DONE, SHORT CIRCUTING ', ja_srt
            return
        update_dones(donefile, ja_srt)

        print '\t GETTING FILE ALIGNMENTS FOR ', ja_srt
        en_srts = get_file_alignments(ja_srt, os.path.join(title_root, 'en'))
        print '\t ALIGNED EN FILES FOR ', ja_srt
        for en_srt in en_srts:
            print '\t\t ', en_srt

        print '\t BUILDING SUBTITLE ALIGNER FOR...', ja_srt
        a = Aligner(ja_srt)
        print '\t SUBTITLE ALIGNER BUILT...', ja_srt

        print '\t HARVESTING SUBS FROM', ja_srt
        alignments = []
        for en_subfile in en_srts:
            print '\t\t MATCHING WITH ', en_subfile
            a.load(en_subfile)
            for pair in a.solve_v3():
                alignments.append(pair)

        if len(alignments) == 0:
            print 'NO ALIGNMENTS FOR ', ja_srt, en_srts
            return
        en = ''
        ja = ''
        t = ''
        for en_s, ja_s, sim, trans in alignments:
            t += str(sim) + "|" + trans + '\n' 
            en += en_s + '\n'
            ja += ja_s + '\n'
        title = title_root.split('/')[1]
        print '\t WRITING RESULTS TO ', title + '_en_subs'
        with open(title + '_en_subs', 'a') as f:
            f.write(en.encode('utf8'))
        print '\t WRITING RESULTS TO ', title + '_trans_subs'
        with open(title + '_trans_subs', 'a') as f:
            f.write(t.encode('utf8'))
        print '\t WRITING RESULTS TO ', title + '_ja_subs'
        with open(title + '_ja_subs', 'a') as f:
            f.write(ja.encode('utf8'))
    except Exception as e:
        print 'EXCEPTION  ON ', ja_srt
        with open('EXCEPTIONS', 'a') as f:
            f.write(str(e))


def generate_subfiles(root_dir):
    """ spits out ja files and aligned en files
    """
    out = []
    for title_dir in os.listdir(root_dir):
        for ja_subfile in os.listdir(os.path.join(root_dir, title_dir, 'ja')):
            out.append((os.path.join(root_dir, title_dir, 'ja', ja_subfile), \
                        os.path.join(root_dir, title_dir)))
    random.shuffle(out)
    for (ja, title) in out:
        yield ja, title


def main(data_loc, en_out, ja_out, num_threads, donefile):
    root = data_loc
    os.system("find %s -type f -name '*.DS_Store' -delete" % root)

    Parallel(n_jobs=num_threads)(delayed(extract_subs)(ja, title, donefile) \
                                     for (ja, title) in generate_subfiles(data_loc))

    # Parallel makes its own namespace, so i couldn't modify a shared
    # dictionary or anything. had to split and join.
    print 'JOINING RESULTS...'
    split_order = []
    for f in os.listdir('.'):
        if '_en_subs' in f:
            split_order.append(f.split('_')[0])   # TODO - BETER SPLITTER

    en_cat = 'cat ' + ' '.join('%s_en_subs' % title for title in split_order) + ' > %s' % en_out
    ja_cat = 'cat ' + ' '.join('%s_ja_subs' % title for title in split_order) + ' > %s' % ja_out

    os.system(ja_cat)

    os.system(en_cat)

    print 'NOT CLEANING UP...'
#    os.system('rm *_subs')

    print 'DONE'

                                                                                                                                     
if __name__ == '__main__':
    args = process_command_line()
    main(args.data_loc, args.en_out, args.ja_out, args.num_threads, args.donefile)

