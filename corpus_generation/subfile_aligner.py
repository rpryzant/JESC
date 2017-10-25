"""
=== Description
The Aligner class can align japanese/english subtitle files, and 
    provides a generator to let users iterate over the matched
    caption pairs.

=== USAGE

a = Aligner(ja_srt_file)
a.load(en_srt_file)

for en_caption, ja_caption, similarity_score, approx_translation in a.solve_v3():
    # do what you want
"""
# -*- coding: utf-8 -*-
import string
import pysrt
import re
from tqdm import tqdm
import collections
import os
from tf_idf import TF_IDF
import numpy as np
from utils import clean_caption

class Aligner():
    def __init__(self, ja_file):
        self.ja_file = ja_file
        self.ja = pysrt.open(ja_file)
        self.ja_start = self.first_content_caption(self.ja)
        self.ja_translations = self.build_ja_translations()


    def build_ja_translations(self, min_trans=500):
        """ builds approximate translations for each caption
            in self.ja_file

            returns: [ (translation, caption) ]
        """
        out = []
        for x in range(self.ja_start, min(min_trans, len(self.ja))):
            caption = clean_caption(self.ja[x].text)
            if len(caption) > 0:
                out.append(( self.translate(caption), caption) )
        return out


    def load(self, en_file):
        """ load an en subfile (.srt) into the aligner
        """
        self.en_file = en_file
        self.en = pysrt.open(en_file)
        self.en_start = self.first_content_caption(self.en)
        # build tf-idf vectors for each caption
        self.tf_idf = TF_IDF(en_file)        


    def first_content_caption(self, subfile):
        """ finds the first caption with a real caption.
            this is typically the first caption at a "real" time (i.e. not at 2:00)
        """
        for i, sub in enumerate(subfile):
            if sub.start.milliseconds != 0:
                return i


    def translate(self, caption):
        """ produces an approximate translation of a cleaned ja caption
         
            returns: translation (str)
        """        
        try:
            # delete whitespace from ja
            ja = caption.replace(' ', '').encode('utf8')
            ja = ja.replace('\xe3\x80\x80', '')
            ja = ja.strip()
            if len(ja) == 0:
                return None
            # get trans
            cmd = "./trans ja: " + ja
            result = os.popen(cmd).read().split('\n')[-2].split(',')[0]

            # parse trans
            result = ''.join([char for char in result if char in string.printable])
            result = result[7:-4].lower()
            return result

        except: 
            return ''


    def get_caption_matches(self):
        """ match up en and ja srt files
            returns: a list of (en caption, ja caption) tuples

            TODO - use trans as reference for in tf-idf matching because
                   those are your pivots anyway....
        """
        j = self.ja_start
        e = self.en_start
        delta = (abs((len(self.ja) - j) - (len(self.en) - e)))
        matches = []
        for i, (trans, ja_sub) in enumerate(self.ja_translations):
            if e+i > len(self.en):
                break
            candidates = []
            for j in range(max(0, e+i-10), min(len(self.en), e+i+delta)):
                en_sub = clean_caption(self.en[j].text)
                sim, en_vec, trans_vec =  self.tf_idf.similarity(en_sub, trans)
                subs = (en_sub, ja_sub)
                candidates.append( (sim, j, subs, trans, en_vec, trans_vec) )
            candidates = sorted(candidates)[::-1]
            if len(candidates) > 0:
                matches.append(candidates[0])
        return matches


    def solve_v3(self):
        """ main alignment logic. for each ja caption, take its approximate translation
            and look around for nearby en captions with high tf-idf similarity
            
            yields: (en, ja) caption pairs
        """
        def get_ratio_cutoff(matches):
            len_ratios = [len(m[2][0]) * 1.0 / len(m[2][1]) for m in matches]
            ratio_mean = np.mean(len_ratios)
            ratio_std = np.std(len_ratios)
            return ratio_mean + ratio_std

        def get_sim_cutoff(matches):
            sims = [m[0] for m in matches]
            sim_mean = np.mean(sims)
            sim_std = np.std(sims)
            return sim_mean + (0.50 * sim_std)

        matches = self.get_caption_matches()

        ratio_cutoff = get_ratio_cutoff(matches)
        sim_cutoff = get_sim_cutoff(matches)

        print '\t\t SPEWING MATCHES FOR', self.ja_file, self.en_file
        for match in matches:
            sim, e, (en, ja), trans, en_vec, trans_vec = match

            len_ratio = len(en) * 1.0 / len(ja)

            if sim > sim_cutoff and len_ratio < ratio_cutoff:
                print 'spewing ', en, ja, sim, trans
                yield en, ja, sim, trans


