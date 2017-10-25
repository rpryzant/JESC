# Learn BPE across both corpora

A_PATH=$1
B_PATH=$2
VOCAB_SIZE=$3

spm_train \
  --input=${A_PATH},${B_PATH} \
  --model_prefix=bpe \
  --vocab_size=${VOCAB_SIZE} \
  --model_type=bpe

