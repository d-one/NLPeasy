from enum import Enum

class Lang(Enum):
    ## Format is: 2-letter-code = ( ElasticCode, [spacymodels] )
    DE = ('german', ['de_core_news_sm','de_core_news_md'])
    EL = ('greek', ['el_core_news_sm','el_core_news_md'])
    EN = ('english', ['en_core_web_sm','en_core_web_md','en_core_web_lg','en_vectors_web_lg'])
    ES = ('spanish', ['es_core_news_sm','es_core_news_md'])
    FR = ('french', ['fr_core_news_sm','fr_core_news_md'])
    IT = ('italian', ['it_core_news_sm'])
    NL = ('dutch', ['nl_core_news_sm','nl_core_news_md'])
    PT = ('portuguese', ['pt_core_news_sm'])
    XX = (None, ['xx_ent_wiki_sm'])

    def __init__(self, elastic, spacy_models):
        self.code = self.name
        self.elastic = elastic
        self.spacy_models = spacy_models
    @property
    def spacy_models_installed(self):
        from importlib.util import find_spec
        return [ i for i in self.spacy_models if find_spec(i) is not None ]
