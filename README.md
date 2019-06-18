NLPeasy
=======

Build NLP pipelines the easy way


* Free software: Apache Software License 2.0


Installation
------------

To install this module in Dev-mode, i.e. change files and reload module:
```bash
git clone https://github.com/nlpeasy/nlpeasy
pip install -e .
```

In Jupyter you should be able to use:
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
#
#   ne.start_elastic_on_docker('nlp', version='6.3.2', mountVolumePrefix=None)
#
# takes a couple of minutes in the backgroud to be ready...
# mountVolumePrefix=./elastic/ would mount elastic/elastic-data into the container to survive container restarts

# read texts with subject, message and 
nips = pd.read_pickle('./nips.pickle')
# or get e.g. NIPS abstracts using:
# wget --mirror -E -l 2 --no-parent https://papers.nips.cc/
# in the future: ne.crawl('papers.nips.cc', '.')
nips = ne.parse_html('./papers.nips.cc/paper/*.html', select={
    'title': 'title',
    'message': 'p.abstract',
    'author': 'li.author a'
    })
nips['year'] = pd.to_datetime(nips.meta_citation_publication_date+'-12-01')
nips.to_pickle('./nips.pickle)

# setup stages in the NLP pipeline and set textfields
pipeline = ne.Pipeline(index='nips', textCols=['message','title'], suggests='message_subj', dateCol='year')

pipeline.add(ne.RegexTag(r'\$([^$]+)\$', ['message'], 'math'))
pipeline.add(ne.VaderSentiment('message', 'sentiment'))

# This uses `en_core_web_sm` so download the model first via:
# python -m spacy download en_core_web_sm
pipeline.add(ne.SpacyEnrichment(nlp='en_core_web_sm', cols=['message','title']))

# Future possibilities
# pipeline.add(ne.SynonymTags(['Neural', 'Bayesian'], topn=10), ['message'], 'hypekeyword')
# pipeline.add(ne.Split(', '), ['author'])

# start and setup elastic and kibana
pipeline.setup_elastic()

nips_enriched = pipeline.process(nips, writeElastic=True)

# open Kibana in webbrowser
ne.showKibana()
```

Features
--------

* TODO

Credits
-------

This package was created with [Cookiecutter](<https://github.com/audreyr/cookiecutter>) and the [`audreyr/cookiecutter-pypackage`]<https://github.com/audreyr/cookiecutter-pypackage> project template.
