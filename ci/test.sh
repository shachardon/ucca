#!/usr/bin/env bash

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
    python parsing/parse.py -c sparse --maxwordsexternal=5000 -WeLMCb pickle/dev/*7* -t pickle/train/*7*
    ;;
dense)
    python parsing/parse.py -c dense --maxwordsexternal=5000 -WeLMCb pickle/dev/*7* -t pickle/train/*7*
    ;;
mlp)
    python parsing/parse.py -c mlp --maxwordsexternal=5000 -WeLMCb pickle/dev/*7* -t pickle/train/*7* --dynet-mem=3072
    ;;
bilstm)
    python parsing/parse.py -c bilstm --maxwordsexternal=5000 -WeLMCb pickle/dev/*7* -t pickle/train/*7* --dynet-mem=3072
    ;;
tune)
    export PARAMS_NUM=5
    python parsing/tune.py doc/toy.xml -t doc/toy.xml --maxwordsexternal=5000 --dynet-mem=3072 || exit 1
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
