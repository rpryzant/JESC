# generate your own splits with this file

EN=$1
JA=$2
TEST=$3
DEV=$4
BOTH=$((DEV+TEST))

echo 'Test size:' ${TEST}
echo 'Dev size:' ${DEV}
echo 'Joint size:' ${BOTH}


echo 'shuffling corpus...'
paste ${EN} ${JA} | shuf > corpus.shuf

echo 'separating into en/ja'
cat corpus.shuf | cut -f1 > corpus.shuf.en
cat corpus.shuf | cut -f2 > corpus.shuf.ja

echo 'splitting into train/dev/test'
tail -n +${BOTH} corpus.shuf.en > train.en
tail -n +${BOTH} corpus.shuf.ja > train.ja
head -n ${DEV} corpus.shuf.en > dev.en
head -n ${DEV} corpus.shuf.ja > dev.ja
head -n ${BOTH} corpus.shuf.en | tail -n +${TEST}  > test.en
head -n ${BOTH} corpus.shuf.ja | tail -n +${TEST} > test.ja

echo 'cleaning up...'
rm corpus.shuf
rm corpus.shuf.en
rm corpus.shuf.ja
