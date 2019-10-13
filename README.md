[![Travis Build Status](<https://img.shields.io/travis/d-one/nlpeasy/master.svg?style=flat-square&logo=travis-ci&logoColor=white&label=build>)](https://travis-ci.org/d-one/nlpeasy)
[![pypi Version](https://img.shields.io/pypi/v/nlpeasy.svg?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/nlpeasy/)

NLPeasy
=======

Build NLP pipelines the easy way

> **Disclaimer:** This is in Alpha stage, lot of things can go wrong.
> It could possibly change your Elasticsearch Data the API is not fixed yet
> and even the name NLPeasy might change.

* Free software: Apache Software License 2.0


Usage
-----

For this example to completely work you need to have Python at least in Version 3.6 installed.
Also you need to have install and start either
- **Docker** <https://www.docker.com/get-started>, direct download links for
    [Mac (DMG)](https://download.docker.com/mac/stable/Docker.dmg) and
    [Windows (exe)](https://download.docker.com/win/stable/Docker%20for%20Windows%20Installer.exe).
- **Elasticsearch** and **Kibana**:
<https://www.elastic.co/downloads/> or
<https://www.elastic.co/downloads/elasticsearch-oss> (pure Apache licensed version)

Then on the terminal issue:
```bash
python -m venv venv
source venv/bin/activate
pip install nlpeasy scikit-learn
python -m spacy download en_core_web_md
```
The package `scikit-learn` is just used in this example to get the newsgroups data and preprocess it.
The last command downloads a spacy model for the english language -
for the following you need to have at least it's `md` (=medium) version which has wordvectors.

```python
import pandas as pd
import nlpeasy as ne
from sklearn.datasets import fetch_20newsgroups

# connect to running elastic or else start an Open Source stack on your docker
elk = ne.connect_elastic(dockerPrefix='nlp', elkVersion='7.4.0', mountVolumePrefix=None)
# If it is started on docker it will on the first time pull the images (1.3GB)!
# Setting mountVolumePrefix="./elastic-data/" would keep the data of elastic in your
# filesystems and then the data survives container restarts

# read data as Pandas data frame
news_raw = fetch_20newsgroups(remove=('headers', 'footers', 'quotes'))
news_groups = [news_raw['target_names'][i] for i in news_raw['target']]
news = pd.DataFrame({'newsgroup': news_groups, 'message': news_raw['data']})

# setup NLPeasy pipeline with name for the elastic index and set the text column
pipeline = ne.Pipeline(index='news', textCols=['message'], tagCols=['newsgroup'], elk=elk)

pipeline += ne.VaderSentiment('message', 'sentiment')
pipeline += ne.SpacyEnrichment(nlp='en_core_web_md', cols=['message'], vec=True)

# do the pipeline - just for first 100, the whole thing would take 10 minutes
news_enriched = pipeline.process(news.head(10000000), writeElastic=True)

# Create Kibana Dashboard of all the columns
pipeline.create_kibana_dashboard()

# open Kibana in webbrowser
elk.show_kibana()
```

Let's have some fun outside of Elastic/Kibana - but this needs `pip install matplotlib`
```python
import numpy as np
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
grouped = news_enriched.loc[~news_enriched.message_vec.isna()].groupby('newsgroup')
group_vec = grouped.apply(lambda z: np.stack(z.message_vec.values).mean(axis=0))
clust = linkage(np.stack(group_vec), 'ward')
# calculate full dendrogram
plt.figure(figsize=(10, 10))
plt.title('Hierarchical Clustering Dendrogram Newsgroups')
plt.xlabel('sample index')
plt.ylabel('distance')
dendrogram(
    clust,
    leaf_rotation=0.,  # rotates the x axis labels
    leaf_font_size=8.,  # font size for the x axis labels
    labels=group_vec.index,
    orientation='left'
)
plt.show()
```

Installation
------------

Prerequisites:
- Python 3 (we use Python 3.7)
- Elastic: Several possibilities
    - Have Docker installed - needs to have the docker package installed (see below).
    - Install and start Elasticsearch and Kibana:
    <https://www.elastic.co/downloads/> or
    <https://www.elastic.co/downloads/elasticsearch-oss> (pure Apache licensed version)
    - Use any running Elasticsearch and Kibana (on premise or cloud)...
- Pretrained Models: See below for Spacy Language Models and WordVectors

It is recommended to use a virtual environment:
```bash
cd $PROJECT_DIR
python -m venv venv
source venv/bin/activate
```
The source statement has to be repeated whenever you open a new terminal.

Then install
```bash
pip install nlpeasy
```
Or the development version from GitHub:
```bash
pip install --upgrade git+https://github.com/d-one/nlpeasy
```

If you want to use spaCy language models download them (90-200 MB), e.g.
```bash
python -m spacy download en_core_web_md
# and/or
python -m spacy download de_core_news_md
```
If you want to use pretrained [FastText-Wordvectors](https://fasttext.cc/docs/en/pretrained-vectors.html) (each ~7GB):
```bash
curl -O https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip
curl -O https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.de.zip
```

If you want to use Jupyter, install it to the virtual environment:
```bash
pip install jupyterlab
```

### Development
To install this module in Dev-mode, i.e. change files and reload module:
```bash
git clone https://github.com/d-one/nlpeasy
cd nlpeasy
```

It is recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

Install the version in edit mode:
```bash
pip install -e .
```

In Jupyter you can have reloaded code when you change the files as in:
```python
%load_ext autoreload
%autoreload 2
```

Features
--------

* Pandas based pipeline
* Support for any extensions - now includes some for Regex, spaCy, VaderSentiment
* Write results to ElasticSearch
* Automatic Kibana dashboard generation
* Have Elastic started in Docker if it is not installed locally or remotely
* Apache License 2.0

Credits
-------

This package was created with [Cookiecutter](<https://github.com/audreyr/cookiecutter>) and the [`audreyr/cookiecutter-pypackage`]<https://github.com/audreyr/cookiecutter-pypackage> project template.
