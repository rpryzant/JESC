"""
Utility functions (caption cleaning)
"""

import re


def clean_caption(x):
    """ cleans a caption
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

