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

# connect to running elastic or else start an Open Source stack on your docker
elk = ne.connect_elastic(dockerPrefix='nlp', dockerELKVersion='6.3.2', dockerMountVolumePrefix=None)
# If it is started on docker it will on the first time pull the images (1.3GB)!
# BTW, this function is not blocking, i.e. the servers might only be active couple of seconds later.
# Setting dockerMountVolumePrefix="./elastic-data/" keeps the data of elastic in your
# filesystems and then the data survives container restarts

# setup stages in the NLP pipeline and set textfields
pipeline = ne.Pipeline(index='nips', textCols=['message','title'], dateCol='year', elk=elk)

pipeline += ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math')
pipeline += ne.VaderSentiment('message', 'sentiment')
pipeline += ne.SpacyEnrichment(cols=['message','title'])

# do the pipeline
nips_enriched = pipeline.process(nips, writeElastic=True)

# Create Kibana Dashboard of all the columns
pipeline.create_kibana_dashboard()

# open Kibana in webbrowser
elk.show_kibana()
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
