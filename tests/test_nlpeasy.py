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
    elk = ne.connect_elastic(
        docker_prefix="nlp", elk_version="7.4.2", mount_volume_prefix=None
    )
    elk.wait_for()
    return elk


def test_end_to_end(elk):
    """Sample pytest test function with the pytest fixture as an argument."""
    # read data as Pandas data frame
    # nips = pd.read_pickle("data_raw/nips.pickle")
    from sklearn.datasets import fetch_20newsgroups

    news_raw = fetch_20newsgroups()
    news = pd.DataFrame(
        {
            "group": [news_raw["target_names"][i] for i in news_raw["target"]],
            "message": news_raw["data"],
        }
    )

    # setup stages in the NLP pipeline and set textfields
    pipeline = ne.Pipeline(index="news", text_cols=["message"], elk=elk)

    # pipeline += ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math')
    # pipeline += ne.VaderSentiment('message', 'sentiment')
    # pipeline += ne.SpacyEnrichment(cols=['message','title'])

    n = 1000
    # do the pipeline
    news_enriched = pipeline.process(news.head(n), write_elastic=True)

    assert news_enriched.shape[0] == n

    # Create Kibana Dashboard of all the columns
    pipeline.create_kibana_dashboard()

    # open Kibana in webbrowser
    # elk.show_kibana()


@pytest.mark.skipif(
    not Path("data_raw/nips.pickle").exists(),
    reason="Skipping: data not yet publicly available",
)
def test_timerange(elk):
    # read data as Pandas data frame
    nips = pd.read_pickle("data_raw/nips.pickle")

    # setup stages in the NLP pipeline and set textfields
    pipeline = ne.Pipeline(
        index="nips", text_cols=["message", "title"], date_col="year", elk=elk
    )

    pipeline += ne.RegexTag(r"\$([^$]+)\$", ["message"], "math")
    pipeline += ne.VaderSentiment("message", "sentiment")
    # pipeline += ne.SpacyEnrichment(cols=['message', 'title'])

    n = 1000
    # do the pipeline
    nips_enriched = pipeline.process(nips.head(n), write_elastic=True)

    assert nips_enriched.shape[0] == n

    # Create Kibana Dashboard of all the columns
    pipeline.create_kibana_dashboard()

    # open Kibana in webbrowser
    # elk.show_kibana()
