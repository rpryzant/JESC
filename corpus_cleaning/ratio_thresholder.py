"""
=== USAGE
python thresholder.py [corpus file 1] [corpus file 2]

=== INPUTS
This script assumes that each corpus file is a raw list of sentences, 1 per line, and that
the sentences of these corpus files are matched

=== OUTPUTS
Two more corpus files (same name but with the ".cleaned" suffix). These will be the same
as the original inputs, but pairs with outlying length ratios (exceeding the 95th percentile)
will be discarded

"""
import sys
import re
import numpy as np

def ratio(s1, s2):
    return len(s1) * 1.0 / len(s2)

# get ratios
f1 = open(sys.argv[1])
f2 = open(sys.argv[2])
ratios = []
for text_1, text_2 in zip(f1, f2):
    if len(text_1) == 0 or len(text_2) == 0:
        continue
    ratios.append(ratio(text_1, text_2))

# calculate summary statistics
ratios = sorted(ratios)
N = len(ratios) * 1.0
mu = np.mean(ratios)
sd = np.std(ratios)

# use statistics to throw out some pairs
f1.seek(0)
f2.seek(0)
out1 = ''
out2 = ''
for text_1, text_2 in zip(f1, f2):
    if len(text_1) == 0 or len(text_2) == 0:
        continue
    r = ratio(text_1, text_2)
    if (r <  mu - 1.96 * sd) or (r >  mu + 1.96 * sd):
        continue
    out1 += text_1.strip() + '\n'
    out2 += text_2.strip() + '\n'

# write remaining pairs
f = open(sys.argv[1] + '.cleaned', 'w')
f.write(out1)
f.close()
f = open(sys.argv[2] + '.cleaned', 'w')
f.write(out2)
f.close()






