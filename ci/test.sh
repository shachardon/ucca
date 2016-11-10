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
    python parsing/parse.py -c sparse -WeLMCbs pickle/dev -t pickle/train
    ;;
dense)
    python parsing/parse.py -c dense -w word_vectors/sskip.100.vectors.txt -WeLMCbs pickle/dev -t pickle/train
    ;;
nn)
    python parsing/parse.py -c nn -WeLMCbs pickle/dev -t pickle/train -I10 --layerdim=100 --batchsize 500
    ;;
tune)
    export W2V_FILE=word_vectors/sskip.100.vectors.txt
    export PARAMS_NUM=10
    python parsing/tune.py doc/toy.xml -t doc/toy.xml --dynet-mem=3072 || exit 1
    column -t -s, params.csv
    ;;
convert)
    ci/test_convert_all.sh
    ;;
convert_sentences)
    mkdir -p pickle/sentences
    python scripts/standard_to_sentences.py pickle/*.pickle -o pickle/sentences -p "ucca_passage" -b || exit 1
    ci/test_convert_all_sentences.sh || exit 1
    ;;
esac
