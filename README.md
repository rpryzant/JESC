

# JESC Code Release

Welcome to the JESC code release! This repo contains the crawlers, parsers, aligners, and various tools used to create the Japanese-English Subtitle Corpus (JESC). 

* [JESC homepage](https://cs.stanford.edu/~rpryzant/jesc/)
* [JESC paper](https://arxiv.org/abs/1710.10639)


## Requirements
Use pip: `pip install -r requirements.txt`

Additionally, some of the corpus_processing scripts make use of [google/sentencepiece](https://github.com/google/sentencepiece), which has installation instructions on its github page. 


## Instructions

Each file is a standalone tool with usage instructions given in the comment header. These files are organized into the following categories (subdirectories):

* **corpus_generation**: Scripts for downloading, parsing, and aligning subtitles from the internet.

* **corpus_cleaning**: Scripts for converting file formats, thresholding on length ratios, and spellchecking.

* **corpus_processing**: Scripts for manipulating completed datasets, including tokenization and train/test/dev splitting.

## Citation

Please give the proper citation or credit if you use these data:

```
LREC citation
```
