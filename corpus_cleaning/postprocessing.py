"""
=== DESCRIPTION
This file postprocesses english data, removing
noise like leading dashes, non-ascii characters, 
non-english examples, etc

=== USAGE
python postprocessing.py [en file] [ja file] > output

=== INPUTS
"en file" and "ja file" are 1-phrase-per-line parallel text files

=== OUTPUTS
A single file representing a cleaned parallel corpus.
The en and ja phrases in this file are tab-separated


"""
import string
import sys
from tqdm import tqdm
import enchant
import re

dictionary = enchant.Dict("en_US")
VALID_PUNCTUATION = '!#$%&(),.:;?\'[]{}'


def clean_caption(x):
    """ cleans a caption (from corpus_generation/utils.py)
    """
    x = x.strip()                            # strip ends                                                      
    x = x.lower()                            # lowercase                                                            
    
    ja_parens      = re.compile('\xef\xbc\x88.*?\xef\xbc\x89')
    ja_rightarrow  = re.compile('\xe2\x86\x92')
    actor          = re.compile('[\w ]+:')
    unwanted       = re.compile('[*#]')    
    brackets       = re.compile('\<.*?\>|{.*?}|\(.*?\)')
    newlines       = re.compile('\\\\n|\n')
    site_signature = re.compile('.*subtitles.*\n?|.*subs.*\n?', re.IGNORECASE)
    urls           = re.compile('www.*\s\n?|[^\s]*\. ?com\n?')
    msc            = re.compile('\\\\|\t|\\\\t|\r|\\\\r')
    encoding_error = re.compile('0000,0000,0000,\w*?')
    multi_space    = re.compile('[ ]+')

    # to and from unicode for regex to work
    x = unicode(ja_parens.sub('', x.encode('utf8')), 'utf8')
    x = unicode(ja_rightarrow.sub('', x.encode('utf8')), 'utf8')
    x = actor.sub('', x)
    x = unwanted.sub('', x)
    x = brackets.sub('', x)
    x = site_signature.sub('', x)
    x = urls.sub('', x)
    x = msc.sub('', x)
    x = encoding_error.sub('', x)
    x = newlines.sub(' ', x)
    x = multi_space.sub(' ', x)
    x = x.strip()
    
    return x


def percent_english_words(l):
    """ gets the percent fo whitespace-seperated chunks that are english words 
    """
    l = ''.join(c for c in l if c not in string.punctuation)
    words = l.split(' ')
    en_count = 0.0
    i = 0
    for word in words:
        try:
            if dictionary.check(word.strip()):
                en_count += 1
        except:
            pass
        i += 1.0

    percent = en_count/i if i != 0 else 0
    return percent


def is_alpha(c):
    try:
        return c.encode('ascii').isalpha()
    except:
        return False


def safe(char):
    """ tests whether a char is a valid roman character
    """
    if is_alpha(char):
        return True

    if char in VALID_PUNCTUATION:
        return True

    if char == ' ':
        return True

    if char.isdigit():
        return True

    return False


en = open(sys.argv[1])
en_lines = en.readlines()

ja = open(sys.argv[2])
ja_lines = ja.readlines()


for en_l, ja_l in tqdm(zip(en_lines, ja_lines)):
    cleaned_line = en_l.strip('- ').lstrip('.)] ').rstrip(',([ ')
    cleaned_line = ''.join(c for c in en_l if safe(c)).strip().lstrip('.')
    cleaned_line = cleaned_line.replace('  ', ' ').lower().rstrip(',')
    cleaned_line = clean_caption(cleaned_line)

    ja_cleaned = ja_l.lstrip('- ').strip()

    if len(cleaned_line) >= 2 and percent_english_words(cleaned_line) > 0.4:
        print '%s\t%s' % (cleaned_line, ja_cleaned)

