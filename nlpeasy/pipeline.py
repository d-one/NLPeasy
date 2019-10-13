# -*- coding: utf-8 -*-

"""Main module."""


import pandas as pd
import spacy

from . import elastic
from . import kibana
from .util import chunker, Tictoc

class Pipeline(object):
    def __init__(self, index, textCols=None, tagCols=None, numCols=None, geoPointCols = None,
            idCol=None, dateCol=None, suggests=None, elk=None, lang='english', doctype='_doc'):
        self._pipeline = []
        self._index = index
        self._doctype=doctype
        self._textCols = textCols or []
        self._tagCols = tagCols or []
        self._numCols = numCols or []
        self._geoPointCols = geoPointCols or []
        self._ignoreUploadCols = []
        self._dateCol = dateCol
        self._idCol = idCol
        self._suggests = suggests or []
        self._lang = lang
        self.elk = elk
        self._tictoc = Tictoc(output='', additive=True)
        self._min_max = {}
    def add(self, x):
        self._pipeline.append(x)
        x.addingToPipeline(self)
    def __iadd__(self, other):
        self.add(other)
        return self
    def suggests(self, suggestCols):
        self._suggests = suggestCols

    def setup_elastic(self, **kwargs):
        if self.elk is not None:
            self.elk.createIndex(self._index, self._doctype,
                textCols=self._textCols, tagCols=self._tagCols,
                dateCol=self._dateCol, geoPointCols=self._geoPointCols, lang=self._lang, **kwargs)
    def setup_kibana(self, **kwargs):
        visCols = []
        if self._dateCol:
            visCols.append(kibana.DateHistogram(self._dateCol))
        for i in self._tagCols:
            visCols.append(kibana.HorizontalBar(i))
        for i in self._textCols:
            visCols.append(kibana.TagCloud(i))
        for i in self._numCols:
            interval = 0.1
            if i in self._min_max:
                min, max = self._min_max[i]
                interval = (max - min) / 100
            visCols.append(kibana.Histogram(i, interval))
        timeFrom, timeTo = None, None
        if self._dateCol in self._min_max:
            timeFrom, timeTo = self._min_max[self._dateCol]
        self.elk.kibana.setup_kibana(self._index, self._dateCol,
            searchCols=self._textCols, visCols=visCols, dashboard=True,
            timeFrom=timeFrom, timeTo=timeTo, **kwargs)
    def create_kibana_dashboard(self, **kwargs):
        self.setup_kibana(**kwargs)

    def process(self, texts, writeElastic=None, batchSize=1000, returnProcessed=True, progbar=True):
        if writeElastic is None:
            writeElastic = self.elk is not None
        if writeElastic:
            self.setup_elastic()
        results = []

        self.tic('global', 'process')
        for chunk in chunker(texts, batchSize, progbar=progbar):
            x = chunk
            for i,p in enumerate(self._pipeline):
                if not progbar:
                    print(f'Stage {i+1} of {len(self._pipeline)}: {p.name}')
                self.tic(f'Stage {i+1}',p.name)
                x = p.process(x)
                self.toc()
            if writeElastic:
                self.write_elastic(x, chunksize=batchSize, showProgbar=not progbar, setKibanaTimeDefault=False)
            if returnProcessed:
                results.append(x)
        self.toc()
        # return results
        self.tic('global', 'concat results')
        results =  pd.concat(results, sort=False)
        self.toc()

        self.tic('global','min_max_calc')
        # Need to keep track of ranges for kibana to have something ot work on
        cols = self._numCols
        if self._dateCol is not None:
            cols.append(self._dateCol)
        for i in cols:
            self._min_max[i] = (results.loc[:,i].min(),results.loc[:,i].max())
        self.toc()

        return results

    def write_elastic(self, texts, setKibanaTimeDefault=True, chunksize=1000, showProgbar=True):
        self.tic('elastic', 'upload')
        self.elk.loadDocs(index=self._index, doctype=self._doctype, dateCol=self._dateCol, idCol=self._idCol,
                            suggestCol=self._suggests, texts=texts.drop(columns=self._ignoreUploadCols, errors='ignore'), chunksize=chunksize, showProgbar=showProgbar)
        self.toc()
        if setKibanaTimeDefault and self._dateCol is not None:
            self.elk._kibana.set_kibana_timeDefaults(timeFrom=str(texts[self._dateCol].min()), timeTo=str(texts[self._dateCol].max()))
    def tic(self, part, name):
        self._tictoc.tic(f"{part} / {name}")
    def toc(self):
        self._tictoc.toc()

class PipelineStage(object):
    def __init__(self, name=None):
        self.name = type(self).__name__ if name is None else name
    def addingToPipeline(self, pipeline):
        self._pipeline = pipeline
    def doprocess(self, x):
        raise NotImplementedError()
    def tic(self, name):
        self._pipeline.tic(self.name, name)
    def ticwrap(self, iter, name):
        return self._pipeline._tictoc.wrap(iter, f"{self.name} / {name}")
    def toc(self):
        self._pipeline.toc()


class MapToSingle(PipelineStage):
    def __init__(self, col, outCol):
        super(MapToSingle, self).__init__()
        self._col = col if isinstance(col, str) else col[0]
        self._outCol = outCol
    def process(self, text):
        #print(self._col, type(text[self._col]))
        target = text[self._col].apply(lambda x: self.doprocess(str(x)))
        text = text.copy()
        text.loc[:,self._outCol] = target
        return text

class MapToTags(PipelineStage):
    def __init__(self, cols, outCol):
        super(MapToTags, self).__init__()
        self._cols = [cols] if isinstance(cols, str) else cols
        self._outCol = outCol
    def addingToPipeline(self, pipeline):
        super(MapToTags, self).addingToPipeline(pipeline)
        pipeline._tagCols.append(self._outCol)
    def process(self, text):
        target = []
        for i in range(len(text)):
            vals = []
            for c in self._cols:
                vals += (self.doprocess(text[c].iloc[i]))
            target.append(vals)
        text = text.copy()
        text.loc[:,self._outCol] = pd.Series(target)
        return text

class RegexTag(MapToTags):
    def __init__(self, regex='doi:[^ ]+', *args, **kwargs):
        super(RegexTag, self).__init__(*args, **kwargs)
        import re
        self._regex = re.compile(regex)
    def doprocess(self, x):
        y = self._regex.findall(x)
        return y

class VaderSentiment(MapToSingle):
    def __init__(self, *args, **kwargs):
        super(VaderSentiment, self).__init__(*args, **kwargs)
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        self._analyzer = SentimentIntensityAnalyzer()
    def addingToPipeline(self, pipeline):
        super(VaderSentiment, self).addingToPipeline(pipeline)
        pipeline._numCols.append(self._outCol)
    def doprocess(self, x):
        y = self._analyzer.polarity_scores(x)['compound']
        return y

# pipeline = Pipeline(index='nips', textCols=['message','title'])
# pipeline.add(RegexTag(r'\$([^$]+)\$', ['message'], 'math'))
# pipeline.add(VaderSentiment('message', 'sentiment'))
# x = pipeline.process(nips, writeElastic=False)
# x[['math','sentiment']].head(10)

class SynonymTags(MapToTags):
    # def __init__(self, ['Neural', 'Bayesian'], topn=10), ['message'], 'hypekeyword'):
        pass
class Split(MapToTags):
    # def __init__(self, ', '), ['author']):
        pass


###########
## spaCy ##
###########
class MapToNamedTags(PipelineStage):
    def __init__(self, cols, tags, ignoreUploadCols, coerceValsToStr=True):
        super(MapToNamedTags, self).__init__()
        self._cols = [cols] if isinstance(cols, str) else cols
        self._tags = tags
        self._outCols = [ c+'_'+k for c in self._cols for k in tags ]
        self._ignoreUploadCols = [ c+'_'+k for c in self._cols for k in ignoreUploadCols ]
        self._coerceValsToStr = coerceValsToStr
    def addingToPipeline(self, pipeline):
        super(MapToNamedTags, self).addingToPipeline(pipeline)
        # TODO discern between tagCols and numCols...
        pipeline._tagCols.extend(self._outCols)
        pipeline._ignoreUploadCols.extend(self._ignoreUploadCols)
    def process(self, text):
        target = [ text ]
        for c in self._cols:
            x = text[c]
            if self._coerceValsToStr:
                # WORKAROUND
                # spacy.pipe has a bug where '' gives an assertion error (unflatten) if
                # it is on the end of the pipeleine... however ' ' seems to be ok.
                x = x.fillna(' ').astype(str)
            y = self.doprocess(x)
            y = pd.DataFrame(y, index=text.index).rename(mapper=lambda x: c+'_'+x, axis=1)
            target.append(y)
        text = pd.concat( target, axis=1, sort=False)
        return text


class SpacyEnrichment(MapToNamedTags):
    # =spacy.load('en')
    def __init__(self, nlp='en_core_web_sm', *args, tags=['ents','subj','verb'], posNum=True, vec=False, returnDoc=False,
                batch_size=1000, n_threads=-1, **kwargs):
        super(SpacyEnrichment, self).__init__(*args, tags=tags, ignoreUploadCols=['doc','vec','vec_normalized'], **kwargs)
        self._nlp = spacy.load(nlp) if isinstance(nlp, str) else nlp
        self._posNum = posNum
        self._batch_size = batch_size
        self._n_threads = n_threads
        self._returnDoc = returnDoc
        self._vec = vec
    def doprocess(self, x):
        docs = []
        self.tic("spacy make iter")
        spacy_iter = self._nlp.pipe(x.values, batch_size=self._batch_size,
                                n_threads=self._n_threads)
        self.toc()
        for doc in self.ticwrap(spacy_iter, 'spacy iter'):
            self.tic('process spacy docs')
            ret = { 'wc': len(doc) }
            if ret['wc'] == 0:
                docs.append(ret)
                continue
            if 'ents' in self._tags:
    #             ents = pd.DataFrame({ 'ent': e.text, 'lab': e.label_} for e in doc.ents )
                for e in doc.ents:
                    ret['entity_'+e.label_] = ret.get('entity_'+e.label_, []) + [e.text]
                    ret['ents'] = ret.get('ents', []) + [e.text]

            tok = pd.DataFrame({ 'text': w.text, 'lemma': w.lemma_, 'pos': w.pos_, 'dep': w.dep_} for w in doc )
            if 'subj' in self._tags:
                ret['subj'] = list(tok.lemma.loc[tok.dep.isin(['nsubj','sb'])])
            if 'verb' in self._tags:
                ret['verb'] = list(tok.lemma.loc[tok.pos=='VERB'])

            posNum = tok.pos.value_counts()
            posSel = tok.pos.unique() if self._posNum==True else self._posNum
            for pos in posSel:
                ret[ 'num_'+pos ] = posNum.loc[pos]
            if self._vec:
                if self._vec == True or self._vec == 'unnormalized':
                    ret['vec'] = doc.vector
                if self._vec == True or self._vec == 'normalized':
                    ret['vec_normalized'] = doc.vector / doc.vector_norm if doc.vector_norm != 0 else doc.vector
            if self._returnDoc:
                ret['doc'] = doc
            docs.append(ret)
            self.toc()
        return docs

def nlp_disp(doc, jupyter=True):
    '''Displays Spacy dependency trees (best in jupyter)'''
    return spacy.displacy.render(doc, style='dep', jupyter=jupyter)

