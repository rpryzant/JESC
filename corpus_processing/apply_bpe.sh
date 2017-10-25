# Apply BPE to a corpus


BPE_MODEL=$1
A_PATH=$2

spm_encode --model=${BPE_MODEL} --output_format=piece \
    < ${A_PATH} \
    > ${A_PATH}.bpe
