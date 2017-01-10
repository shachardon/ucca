#!/usr/bin/env bash

export KERAS_BACKEND=theano
case "$TEST_SUITE" in
unit)
    # unit tests
    python -m unittest discover -v || exit 1
    # basic conversion test
    ci/test_convert_toy.sh || exit 1
    # basic parser tests
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -vm model_toy || exit 1
    python parsing/parse.py doc/toy.xml -evm model_toy || exit 1
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -svm model_toy_sentences || exit 1
    python parsing/parse.py doc/toy.xml -esvm model_toy_sentences || exit 1
    python parsing/parse.py -I 10 -t doc/toy.xml -d doc/toy.xml -avm model_toy_paragraphs || exit 1
    python parsing/parse.py doc/toy.xml -esvm model_toy_paragraphs || exit 1
    ;;
sparse)
    python parsing/parse.py -c sparse --maxwordsexternal=5000 -WeLMCbs pickle/dev/*0.pickle -t pickle/train/*0.pickle
    ;;
dense)
    python parsing/parse.py -c dense --maxwordsexternal=5000 -WeLMCbs pickle/dev/*0.pickle -t pickle/train/*0.pickle
    ;;
nn)
    python parsing/parse.py -c nn --maxwordsexternal=5000 -WeLMCbs pickle/dev/*0.pickle -t pickle/train/*0.pickle --nbepochs 3 --layerdim=100 --batchsize 500
    ;;
tune)
    export PARAMS_NUM=5
    python parsing/tune.py doc/toy.xml -t doc/toy.xml --maxwordsexternal=5000 || exit 1
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
