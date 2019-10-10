#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `NLPeasy` package."""

import pytest


import nlpeasy as ne
import pandas as pd

@pytest.fixture(scope="session")
def elk():
    """The ELK stack class to use.

    Reuse the same elk among the whole testing session by setting scope="session"
    """
    elk = ne.connect_elastic(dockerPrefix='nlp', elkVersion='7.4.0', mountVolumePrefix=None)
    return elk


def test_end_to_end(elk):
    """Sample pytest test function with the pytest fixture as an argument."""
    # read data as Pandas data frame
    nips = pd.read_pickle("data_raw/nips.pickle")

    # setup stages in the NLP pipeline and set textfields
    pipeline = ne.Pipeline(index='nips', textCols=['message','title'], dateCol='year', elk=elk)

    pipeline += ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math')
    # pipeline += ne.VaderSentiment('message', 'sentiment')
    # pipeline += ne.SpacyEnrichment(cols=['message','title'])

    # do the pipeline
    nips_enriched = pipeline.process(nips.head(100), writeElastic=True)

    # Create Kibana Dashboard of all the columns
    #pipeline.create_kibana_dashboard()

    # open Kibana in webbrowser
    #elk.show_kibana()
