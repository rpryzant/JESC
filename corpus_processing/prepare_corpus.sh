# generate your own splits with this file

EN=$1
JA=$2
TEST=$3
DEV=$4
BOTH=$((DEV+TEST))
VOCAB_SIZE=$5

echo 'Test size:' ${TEST}
echo 'Dev size:' ${DEV}
echo 'Joint size:' ${BOTH}

echo 'Training BPE...'
spm_train \
  --input=${EN},${JA} \
  --model_prefix=bpe \
  --vocab_size=${VOCAB_SIZE} \
  --model_type=bpe

echo 'shuffling corpus...'
paste ${EN} ${JA} | shuf > corpus.shuf

echo 'separating into en/ja'
cat corpus.shuf | cut -f1 > corpus.shuf.en
cat corpus.shuf | cut -f2 > corpus.shuf.ja

echo 'splitting into train/dev/test'
tail -n +${BOTH} corpus.shuf.en > train.en
tail -n +${BOTH} corpus.shuf.ja > train.ja
head -n ${DEV} corpus.shuf.en > val.en
head -n ${DEV} corpus.shuf.ja > val.ja
head -n ${BOTH} corpus.shuf.en | tail -n +${TEST}  > test.en
head -n ${BOTH} corpus.shuf.ja | tail -n +${TEST} > test.ja

echo 'applying BPE...'
for DATASET in corpus.shuf.en corpus.shuf.ja train.en train.ja val.en val.ja test.en test.ja
do
    spm_encode \
	--model=bpe.model \
        --output_format=piece \
	< $DATASET > $DATASET.bpe
done


echo 'cleaning up...'
rm corpus.shuf

