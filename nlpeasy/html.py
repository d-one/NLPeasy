# -*- coding: utf-8 -*-

"""Main module."""


import glob
import pandas as pd
from .util import Progbar

try:
    import bs4
except ImportError:
    raise Exception(
        "Please instell BeautifulSoup4 to for parse_html to work: pip install beautifulsoup4"
    )


def parse_html(
    file,
    select={},
    limit=None,
    autounbox=True,
    add_meta_names=True,
    meta_names_prefix="meta_",
    tags=["h1", "h2", "h3", "b", "em"],
):
    """
    Parse HTML from file:

    >>> parse_html('./papers.nips.cc/paper/*.html', select={
    ... 'title': 'title',
    ... 'message': 'p.abstract',
    ... 'author': 'li.author a'
    ... }).apply(year='_.meta_citation_publication_date')
    """
    files = glob.glob(file)
    rows = []
    progbar = Progbar(len(files))
    for i, fname in enumerate(files):
        cols = {}
        # print(f"Parsing file {fname}")
        if limit is not None and limit <= i:
            break
        with open(fname) as fp:
            soup = bs4.BeautifulSoup(fp)
        for k, v in select.items():
            x = soup.select(v)
            cols[k] = [_.get_text() for _ in x]
        rows.append(cols)
        if add_meta_names:
            for meta in soup.find_all("meta"):
                if "name" in meta.attrs and "content" in meta.attrs:
                    n = meta_names_prefix + meta.attrs["name"]
                    if n not in cols:
                        cols[n] = []
                    cols[n].append(meta.attrs["content"])
        cols["body"] = soup.get_text()
        for tag in tags:
            cols[tag] = [_.get_text() for _ in soup.find_all(tag)]
        cols["a"] = [_["href"] for _ in soup.find_all("a")]
        progbar.add(1)

    all_cols = set(k for _ in rows for k in _.keys())
    if autounbox:
        for col in all_cols:
            for r in rows:
                if col in r and len(r[col]) > 1:
                    break
            else:
                for r in rows:
                    if col in r and len(r[col]) == 1:
                        r[col] = r[col][0]
        lens = {k: len for k in all_cols}  # noqa: F841

    return pd.DataFrame(rows)
