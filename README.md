NLPeasy
=======

Build NLP pipelines the easy way

> **Disclaimer:** This is in Alpha stage, lot of things can go wrong.
> It could possibly mess with your docker containers and change your Elasticsearch Data!
>
> Also the API is very instable and even the name NLPeasy might soon change.

* Free software: Apache Software License 2.0


Installation
------------

Prerequisites:
- Python 3 (we use Python 3.7)
- Elastic: Several possibilities
    - Have Docker installed - needs to have the docker package installed (see below).
    - Install and start Elasticsearch and Kibana from <https://www.elastic.co/downloads/>
    - Configure any running Elasticsearch and Kibana (on premise or cloud)...

It is recommended to use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```
The source statement has to be repeated whenever you open a new terminal.

Then install this version
```bash
pip install --upgrade git+https://github.com/nlpeasy/nlpeasy
```

If you use the docker installation you also need to install the python-docker interface to the installed Docker:
```bash
pip install docker
```

If you want to use spaCy language models download them (90-200 MB), e.g.
```bash
python -m spacy download en_core_web_md
# and/or
python -m spacy download de_core_news_md
```

If you want to use Jupyter, install it to the virtual environment:
```bash
pip install jupyterlab
```

### Development
To install this module in Dev-mode, i.e. change files and reload module:
```bash
git clone https://github.com/nlpeasy/nlpeasy
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

Usage
-----

```python
import pandas as pd
import nlpeasy as ne

# start elastic Open Source stack on your docker

ne.start_elastic_on_docker('nlp', version='6.3.2', mountVolumePrefix=None)

# first time this pulls the images (1.3GB)
# and after returning from this function, the elastic will keep spinning up in the background
# mountVolumePrefix="./elastic-data/" would let the data survive container restarts

setup stages in the NLP pipeline and set textfields
pipeline = ne.Pipeline(index='nips', textCols=['message','title'], suggests='message_subj', dateCol='year')

pipeline += ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math')
pipeline += ne.VaderSentiment('message', 'sentiment')
pipeline += ne.SpacyEnrichment(cols=['message','title'])

# start and setup elastic and kibana
pipeline.setup_elastic()

# do the pipeline
nips_enriched = pipeline.process(nips, writeElastic=True)

# Create Kibana Dashboard of all the columns
pipeline.setup_kibana(texts=nips)

# open Kibana in webbrowser
ne.showKibana('jupyter')
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
