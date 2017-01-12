#!/usr/bin/env bash

case "$TEST_SUITE" in
unit)
    # unit tests
    python -m unittest discover -v || exit 1
    # basic conversion test
    ci/test_convert_toy.sh || exit 1
    # basic parser tests
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -m model_toy -v || exit 1
    python parsing/parse.py doc/toy.xml -em model_toy -v || exit 1
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -sm model_toy_sentences -v || exit 1
    python parsing/parse.py doc/toy.xml -esm model_toy_sentences -v || exit 1
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -am model_toy_paragraphs -v || exit 1
    python parsing/parse.py doc/toy.xml -esm model_toy_paragraphs -v || exit 1
    ;;
sparse)
    python parsing/parse.py -c sparse --maxwordsexternal=5000 -WeLMCb pickle/dev/*0.pickle -t pickle/train/*0.pickle
    ;;
dense)
    python parsing/parse.py -c dense --maxwordsexternal=5000 -WeLMCb pickle/dev/*0.pickle -t pickle/train/*0.pickle
    ;;
mlp)
    python parsing/parse.py -c mlp --maxwordsexternal=5000 --layerdim=100 -WeLMCb pickle/dev/*0.pickle -t pickle/train/*0.pickle --dynet-mem=1500
    ;;
bilstm)
    python parsing/parse.py -c bilstm --maxwordsexternal=5000 --layerdim=100 -WeLMCb pickle/dev/*0.pickle -t pickle/train/*0.pickle --dynet-mem=1500
    ;;
tune)
    export PARAMS_NUM=5
    python parsing/tune.py doc/toy.xml -t doc/toy.xml --maxwordsexternal=5000 --dynet-mem=1500 || exit 1
    column -t -s, params.csv
    ;;
convert)
    ci/test_convert_all.sh
    ;;
convert_sentences)
    mkdir -p pickle/sentences
    python scripts/standard_to_sentences.py pickle/*.pickle -o pickle/sentences -b || exit 1
    ci/test_convert_all_sentences.sh || exit 1
    ;;
esac
