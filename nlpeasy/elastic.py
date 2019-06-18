# -*- coding: utf-8 -*-

"""Main module."""


import pandas as pd
import elasticsearch
from . import kibana

from .util import Progbar, chunker

class ElasticStack(object):
    def __init__(self, host='localhost', elasticPort=9200, kibanaPort=5601, protocol='http',
                kibanaHost=None, kibanaProtocol=None, verify_certs=True, **kwargs):
        self._host = host
        self._elasticPort = elasticPort
        self._protocol = protocol
        self._verify_certs = verify_certs

        self._kibana = kibana.Kibana(
            host=self._host if kibanaHost is None else kibanaHost,
            port=kibanaPort,
            protocol=self._protocol if kibanaProtocol is None else kibanaProtocol,
            verify_certs=self._verify_certs
        )

        self._es = None
        self._elasticKwargs = kwargs
    
    @property
    def es(self):
        if self._es is None:
            host = { 'host': self._host, 'port': self._elasticPort, 'use_ssl': self._protocol == 'https',  }
            self._es = elasticsearch.Elasticsearch([host], verify_certs=self._verify_certs, **self._elasticKwargs)
        return self._es
    
    def getAnalysis(self, lang='english', synonyms=None):
        filter_names = []
        if lang == 'english':
            filter_names.append("english_possessive_stemmer")
        filter_names.append('lowercase')
        filters = {
            f"{lang}_stop": {
                "type": "stop",
                "stopwords": f"_{lang}_"
            },
            f"{lang}_stemmer": {
                "type": "stemmer",
                "language": f"{lang}"
            },
        }
        filter_names.extend(filters.keys())
        if lang == 'english':
            filters["english_possessive_stemmer"] = {
                "type": "stemmer",
                "language": "possessive_english"
            }
        if synonyms is not None:
            filters[f"{lang}_synonym"] = {
                "type": "synonym",
                "synonyms": synonyms
                # "synonyms_path": "analysis/synonym.txt"
            }
            filter_names.append(f"{lang}_synonym")

        analyzer = {
                    f"{lang}_syn": {
                                "tokenizer": "standard",
                                "filter": filter_names
                            }

        }
        return filters, analyzer


    # TODO languages, synonyms, 
    def createIndex(self, index='texts',doctype='text',create=True,
            textCols=[], tagCols=[], geoPointCols = [], synonyms=[], dateCol=None, lang='english',
            deleteOld=True, verbose=False):
        # assert lang == 'english'
        properties = {}
        for k in textCols:
            # TODO Make sure that the analyzer is created as f"{lang}_syn":
            properties[k] =  { "type": "text", "fielddata": True, "analyzer": f"{lang}_syn" }
        for k in tagCols:
            properties[k] =  { "type": "keyword" }
        for k in geoPointCols:
            properties[k] =  { "type": "geo_point" }
        properties["suggest"] = { "type" : "completion" }
        mapping = {
            #"_timestamp": {"enabled": "false"},
            "properties": properties
        }
        if create:
            filters, analyzer = self.getAnalysis(lang, synonyms)
            body={
                "settings": {
                    "analysis": {
                        "filter": filters,
                        # {
                        #     "synonym": {
                        #         "type": "synonym",
                        #         "synonyms": synonyms
                        #         # "synonyms_path": "analysis/synonym.txt"
                        #     }
                        # },
                        "analyzer": analyzer,
                        # "analyzer": {
                        #     "english_syn": {
                        #         "tokenizer": "standard",
                        #         "filter": [
                        #             "english_possessive_stemmer",
                        #             "lowercase",
                        #             "english_stop",
                        #             "english_stemmer",
                        #             "synonym"
                        #         ]
                        #     }
                        # }
                    }
                },

                "mappings": {
                    doctype: mapping
                }
            }
            if verbose:
                print(body)
            if deleteOld:
                try:
                    self.es.indices.delete(index)
                except:
                    pass
            self.es.indices.create(index=index, body=body) # , ignore=[]
            return(body)
        else:
            self.es.indices.put_mapping(index=index, doc_type=doctype, body=mapping)
    
    def loadDocs(self, index, texts, doctype='text', dateCol=None, deleteOld=False, chunksize=1000, idCol=None,
                suggestCol=None, showProgbar=True):
        if idCol is None:
            idCol = texts.index
        if deleteOld:
            try:
                self.es.indices.delete(index)
            except:
                pass
        #createIndex(index=index, create=deleteOld)

        for ic, cdf in enumerate(chunker(texts, chunksize, progbar=showProgbar)):
            docs = cdf.to_dict(orient='records')
            for ii, doc in enumerate(docs):
                i = ic * chunksize + ii
                doc = rmNanFromDict(doc)
                if suggestCol in doc:
                    doc['suggest'] = doc[suggestCol]
                try:
                    self.es.index(index=index, doc_type=doctype, id=idCol[i], body=doc)
                except elasticsearch.ElasticsearchException as ex:
                    print(ex)
                    print(doc)
                    print('=' * 80)
    
    def truncate(self, index, doctype='text'):
        self._es.delete_by_query(index, {
            "query" : { 
                "match_all" : {}
            }
        })

def rmNanFromDict(x):
    if isinstance(x, dict):
        y = {}
        for k,v in x.items():
            if isinstance(v, list) or isinstance(v, dict):
                y[k] = rmNanFromDict(v)
            elif not pd.isna(v):
                y[k] = v
        return y
    if isinstance(x, list):
        y = []
        for v in x:
            if isinstance(v, list) or isinstance(v, dict):
                y.append(rmNanFromDict(v))
            elif not pd.isna(v):
                y.append(v)
        return y
    raise Exception("x has to be a list or a dict")

__DEFAULT_STACK = ElasticStack()
def defaultStack():
    return __DEFAULT_STACK
def setDefaultStack(es):
    global __DEFAULT_STACK
    __DEFAULT_STACK = es

