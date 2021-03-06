#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
if __name__ == '__main__':
    import autopath

import codecs
import sys

from alex.utils.config import as_project_path

from alex.corpustools.wavaskey import save_wavaskey
from alex.components.slu.base import CategoryLabelDatabase
from alex.components.asr.utterance import Utterance
from alex.applications.PublicTransportInfoCS.preprocessing import PTICSSLUPreprocessing
from alex.applications.PublicTransportInfoCS.hdc_slu import PTICSHDCSLU

"""
Uses HDC SLU to add DA annotations to input from uniq.trn file
(by default, can be changed by supplying a filename as argument)
and outputs them into uniq.trn.sem.tmp (in the format of uniq.trn.sem)

Outputs annotations in various formats based of output_* variables:
    output_alignment - outputs utterance with inlined aligned DAIs (exclusive, disables other output_* vars)
    output_utterance - outputs original utterance
    output_abstraction - outputs abstracted utterance
    output_da - outputs DA
"""


def main():

    cldb = CategoryLabelDatabase('../data/database.py')
    preprocessing = PTICSSLUPreprocessing(cldb)
    slu = PTICSHDCSLU(preprocessing, cfg={'SLU': {PTICSHDCSLU: {'utt2da': as_project_path("applications/PublicTransportInfoCS/data/utt2da_dict.txt")}}})

    output_alignment = False
    output_utterance = True
    output_abstraction = False
    output_da = True

    if len(sys.argv) < 2:
        fn_uniq_trn = 'uniq.trn'
    else:
        fn_uniq_trn = sys.argv[1]
    fn_uniq_trn_sem = fn_uniq_trn + '.sem.tmp'

    print "Processing input from file", fn_uniq_trn
    uniq_trn = codecs.open(fn_uniq_trn, "r", encoding='utf8')
    uniq_trn_sem = {}
    for line in uniq_trn:
        wav_key, utterance = line.split(" => ", 2)
        annotation = []
        if output_alignment:
            norm_utterance = slu.preprocessing.normalise_utterance(Utterance(utterance))
            abutterance, _, _ = slu.abstract_utterance(norm_utterance)
            abutterance = slu.handle_false_abstractions(abutterance)
            da = slu.parse_1_best({'utt': Utterance(utterance)}).get_best_da()

            max_alignment_idx = lambda _dai: max(_dai.alignment) if _dai.alignment else len(abutterance)
            for i, dai in enumerate(sorted(da, key=max_alignment_idx)):
                if not dai.alignment:
                    print "Empty alignment:", unicode(abutterance), ";", dai

                if not dai.alignment or dai.alignment == {-1}:
                    dai_alignment_idx = len(abutterance)
                else:
                    dai_alignment_idx = max(dai.alignment) + i + 1
                abutterance.insert(dai_alignment_idx, "[{} - {}]".format(unicode(dai), list(dai.alignment if dai.alignment else [])))
            annotation += [unicode(abutterance)]
        else:
            if output_utterance:
                annotation += [utterance.rstrip()]
            if output_abstraction:
                norm_utterance = slu.preprocessing.normalise_utterance(Utterance(utterance))
                abutterance, _ = slu.abstract_utterance(norm_utterance)
                annotation += [abutterance]
            if output_da:
                da = slu.parse_1_best({'utt': Utterance(utterance)}).get_best_da()
                annotation += [unicode(da)]

        uniq_trn_sem[wav_key] = " <=> ".join(annotation)

    print "Saving output to file", fn_uniq_trn_sem
    save_wavaskey(fn_uniq_trn_sem, uniq_trn_sem)


if __name__ == '__main__':
    main()
