#!/usr/bin/env bash

cd $(dirname $0)
mkdir -p converted
for format in conll sdp export "export --tree"; do
    echo === Evaluating $format ===
    if [ $# -lt 1 -o "$format" = "$1" ]; then
        python ../scripts/convert_and_evaluate.py ../pickle/ucca_passage*.pickle -f $format | tee "$format.log"
    fi
done
