#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `NLPeasy` package."""
from pathlib import Path

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


# @pytest.mark.skip("Skipping: dev")
def test_end_to_end(elk):
    """Sample pytest test function with the pytest fixture as an argument."""
    # read data as Pandas data frame
    # nips = pd.read_pickle("data_raw/nips.pickle")
    from sklearn.datasets import fetch_20newsgroups
    news_raw = fetch_20newsgroups()
    news = pd.DataFrame({'group': [news_raw['target_names'][i] for i in news_raw['target']],
                         'message': news_raw['data']
                         })

    # setup stages in the NLP pipeline and set textfields
    pipeline = ne.Pipeline(index='news', textCols=['message'], elk=elk)

    # pipeline += ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math')
    # pipeline += ne.VaderSentiment('message', 'sentiment')
    # pipeline += ne.SpacyEnrichment(cols=['message','title'])

    N = 1000
    # do the pipeline
    news_enriched = pipeline.process(news.head(N), writeElastic=True)

    assert news_enriched.shape[0] == N

    # Create Kibana Dashboard of all the columns
    pipeline.create_kibana_dashboard()

    # open Kibana in webbrowser
    #elk.show_kibana()

@pytest.mark.skipIf(not Path('../data_raw/nips.pickle').exists(), "Skipping: data not yet publicly available")
def test_timerange(elk):
    # read data as Pandas data frame
    nips = pd.read_pickle("data_raw/nips.pickle")

    # setup stages in the NLP pipeline and set textfields
    pipeline = ne.Pipeline(index='nips', textCols=['message', 'title'], dateCol='year', elk=elk)

    pipeline += ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math')
    pipeline += ne.VaderSentiment('message', 'sentiment')
    # pipeline += ne.SpacyEnrichment(cols=['message', 'title'])

    N = 1000
    # do the pipeline
    nips_enriched = pipeline.process(nips.head(N), writeElastic=True)

    assert nips_enriched.shape[0] == N

    # Create Kibana Dashboard of all the columns
    pipeline.create_kibana_dashboard()

    # open Kibana in webbrowser
    # elk.show_kibana()

