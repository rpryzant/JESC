"""
Many subtitle files have weird ass encodings like SHIFT-JIS. 
This python script replaces every file it's piped with good 'ole UTF-8 .

=== EXAMPLE USAGE: recursively converts everything in given directory:
find ~/Dir/with/files/ -type f | python all_to_utf8.py

"""
import sys
import os
from tqdm import tqdm
from multiprocessing import Process




def to_utf8(fp, encodings):
    """Given a file path, converts that file in-place to utf-8
    """
    def get_charset(fp):
        """ detect encoding of a file """
        # TODO - LOCKING ON head.tmp
        tmp = os.system('head %s > head.tmp' % fp)
        output = os.popen('chardetect head.tmp').read()
        os.system('rm head.tmp')        
        charset = output.split(':')[1].strip().split(' ')[0]
        return charset.upper()

    # if that character set is supported by iconv, convert it
    try:
        charset = get_charset(fp)
        if charset in encodings:
            os.system('iconv -f %s -t UTF-8 "%s" > "%s"' % (charset, fp, fp + '.utf8'))
            os.system('mv "%s" "%s"' % (fp + '.utf8', fp))
            print 'CONVERTED \n\t to "%s" \n\t encoding was: %s' % (fp, charset)
        else:
            raise Exception
    except Exception:
        print 'SKIPPED \n\t %s' % fp


if __name__ == '__main__':
    # get supported encodings
    os.system('iconv -l > tmp')
    supported_encodings = [w.upper() for l in open('tmp').readlines() for w in l.strip().split()]

    # run concurrently 
    MAX_PROCESSES = 4
    processes = set()
    files = [line.strip() for line in sys.stdin]

    for file in tqdm(files):
        p = Process(target=to_utf8, args=(file, supported_encodings,))
        p.start()
        processes.add(p)
        while len(processes) >= MAX_PROCESSES:
            processes.difference_update([p for p in processes if not p.is_alive()])

    # cleanup
    os.system('rm tmp')
