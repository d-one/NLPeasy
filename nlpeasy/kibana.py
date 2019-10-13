# -*- coding: utf-8 -*-

"""Kibana module."""


import pandas
import requests
import json
from . import util

class Kibana(object):
    def __init__(self, host='localhost', port=5601, protocol='http',
                verify_certs=True, **kwargs):
        self._host = host
        self._port = port
        self._protocol = protocol
        self._verify_certs = verify_certs
        self._defaultIndexPatternUID = None
        self._defaultSearchUID = None
    def kibanaUrl(self, path=""):
        # TODO maybe URLEncode path?
        if path and path[0] != '/':
            # TODO Warn about missing initial '/'?
            path = '/'+path
        return f"{self._protocol}://{self._host}:{self._port}{path}"
    def alive(self, verbose=True):
        resp = requests.head(self.kibanaUrl())
        return resp.status_code == 200

    def show_kibana(self, how=None, *args, **kwargs):
        if how is None:
            how = 'jupyter' if util.IS_JUPYTER else 'webbrowser'
            # TODO can we figure out "non-interactive" to put how='print' then?
        how = how if isinstance(how, list) else [how]
        url = self.kibanaUrl(*args, **kwargs)
        if 'print' in how:
            print(f"Open: {url}")
        if 'webbrowser' in how:
            import webbrowser
            webbrowser.open(url)
        if 'jupyter' in how or 'ipython' in how:
            from IPython.core.display import HTML
            return HTML(self._repr_html_())

    def __repr__(self):
        return f"Kibana on {self.kibanaUrl()}"

    def _repr_html_(self):
        return f"Kibana on <a href='{self.kibanaUrl()}'>{self.kibanaUrl()}</a>"

    def getKibanaSavedObjects(self, type='index-pattern', search=None, fields=None):
        type = '&type=' + type if type else ''
        search = '&search=' + search if search else ''
        fields = '&fields=' + fields if fields else ''
        resp = requests.get(self.kibanaUrl(f'/api/saved_objects/_find?{type}{search}{fields}'))
        resp.raise_for_status()
        result = resp.json()['saved_objects']
        return result
    def postKibanaSavedObject(self, type, attributes, id=None):
        body = { "attributes": attributes }
        id = "/"+id if id else ""
        result = requests.post(self.kibanaUrl(f'/api/saved_objects/{type}{id}?overwrite=true'), headers={"kbn-xsrf": "true"}, json=body)
        result.raise_for_status()
        # return result.json()
        return result.json()['id'], result.json()
    def deleteKibanaSavedObject(self, type, uid):
        u = self.kibanaUrl(f'/api/saved_objects/{type}/{uid}')
        resp = requests.delete(u, headers={"kbn-xsrf": "true"})
        resp.raise_for_status
        print(resp.json())
        return resp.json()

    def truncateKibanaSavedObjects(self, types=['dashboard','visualization','search','index-pattern'], search=None):
        for t in types:
            if search is not None and t=='index-pattern_________':
                continue
            objs = self.getKibanaSavedObjects(type=t, fields='name', search=search)
            print(f'deleting {len(objs)} objects of type {t}...')
            for i in objs:
                # print(i['id'])
                self.deleteKibanaSavedObject(t, i['id'])
        print('finished deleting')

    def getKibanaConfig(self, name=None, onlyLastSetValue=True, defaultValue=None):
        assert onlyLastSetValue
        config = self.getKibanaSavedObjects('config')
        # TODO need to implement for onlyLastSetValue=False as well or warn if multiple values?
        result = dict()
        for i in config:
            c = i['attributes']
            result.update(c)
        if name is not None:
            if name in result:
                return result[name]
            else:
                return defaultValue
        return result

    def getSavedObjectIfExists(self, type, title, ifexists):
        for i in self.getKibanaSavedObjects(type, title, 'title'):
            if i['attributes']['title'] == title:
                # it exists already
                if ifexists == 'return_existing':
                    print(f"reusing {type} {title}")
                    return i['id'], None
                if ifexists == 'error':
                    raise ValueError(f"{type} {title} already exists!")
                if ifexists == 'overwrite':
                    self.deleteKibanaSavedObject(type, i['id'])
                if ifexists != 'add':
                    raise ValueError(f"ifexists={ifexists} not understood!!")
        return False

    def addKibanaConfig(self, name, value, addToList=False, id=None):
        assert not addToList
        attributes = { name: value }
        res = self.postKibanaSavedObject('config', attributes, id=id)
        return res
    def addKibanaIndexPattern(self, indexPattern, timeField=None, setDefaultIndexPattern=True, ifexists='return_existing'):
        uid = self.getSavedObjectIfExists('index-pattern', indexPattern, ifexists)
        if uid:
            return uid, None
        attributes = {
            "title": indexPattern,
        }
        if timeField is not None:
            attributes["timeFieldName"] = timeField
        uid, result = self.postKibanaSavedObject('index-pattern', attributes)
        if setDefaultIndexPattern:
            self._defaultIndexPatternUID = uid

        return uid, result

    def addKibanaSearch(self, title, columns, description=None, sort=None, setDefaultSearch=True, indexPatternUID=None, ifexists='return_existing'):
        if indexPatternUID is None:
            indexPatternUID = self._defaultIndexPatternUID
        uid = self.getSavedObjectIfExists('search', title, ifexists)
        if uid:
            return uid, None
        searchSourceJSON = {
            "index": indexPatternUID,
            # "highlightAll": True,
            # "version": True,
            "query":{"query":"","language":"kuery"},
            "filter":[]
        }
        attributes = {
            "title": title, 'columns': columns,
            'kibanaSavedObjectMeta': {'searchSourceJSON': json.dumps(searchSourceJSON)}
        }
        if description is not None:
            attributes['description'] = description
        if sort is not None:
            attributes['sort'] = sort
        uid, res = self.postKibanaSavedObject(type='search', attributes=attributes)
        if setDefaultSearch:
            self._defaultSearchUID = uid
        return uid, res
    def addVisualization(self, title, viz, indexPatternUID=None, ifexists='return_existing'):
        if indexPatternUID is None:
            indexPatternUID = self._defaultIndexPatternUID
        # visState = {
        #     'aggs':[
        #         {'id': '1', 'schema':'metric', 'type': 'count'},
        #         {
        #             'id': '2', 'schema':'segment', 'type': 'terms',
        #             'params': {'field': field, 'size': size, 'order': 'desc', 'orderBy': '1',  }
        #         },
        #     ],
        #     'params': {
        #         'type': 'histogram'
        #     },
        #     'title': title,
        #     'type': visType,
        # }
        assert isinstance(viz, Visualization)
        uid = self.getSavedObjectIfExists('visualization', title, ifexists)
        if uid:
            return uid, None
        visState = viz.visState(title)
        searchSourceJSON = {
            "index":indexPatternUID,
            "filter":[],
            "query":{"language":"kuery","query":""}
        }
        uid, res = self.postKibanaSavedObject('visualization', attributes={
            'title': title, 'visState': json.dumps(visState), 'uiStateJSON': '{"vis":{"legendOpen":false}}',
            'kibanaSavedObjectMeta': {'searchSourceJSON': json.dumps(searchSourceJSON)}
        })
        return uid, res
    def addDashboard(self, title, searchUID, visUIDs, timeFrom=None, timeTo=None, nVisCols=3, visW=16, visH=16, searchW=48, searchH=16, ifexists='return_existing'):
        uid = self.getSavedObjectIfExists('dashboard', title, ifexists)
        if uid:
            return uid, None
        panels = [{
            'panelIndex': '1',
            'gridData': {'x': 0, 'y': 0, 'w': searchW, 'h': searchH, 'i': '1'},
            'version': '6.3.2',
            'type': 'search',
            'id': searchUID,
            'embeddableConfig': {}
        }]
        for i, v in enumerate(visUIDs):
            ix, iy = i % nVisCols, i // nVisCols
            x, y = ix*visW , searchH + iy*visH
            # print(ix,iy, x,y)
            iStr = str(i+2)
            panels.append({
                'panelIndex': iStr,
                'gridData': {'x': x, 'y': y, 'w': visW, 'h': visH, 'i': iStr},
                'version': '6.3.2',
                'type': 'visualization',
                'id': v,
                'embeddableConfig': {}
            })
        attributes = {
            'title': title,
        #      'hits': 0,
            'description': '',
            'panelsJSON': json.dumps(panels),
            'optionsJSON': '{"darkTheme":false,"useMargins":true,"hidePanelTitles":false}',
        #      'version': 1,
        #      'refreshInterval': {'display': 'Off', 'pause': False, 'value': 0},
            'kibanaSavedObjectMeta': {'searchSourceJSON': '{"query":{"query":"","language":"kuery"},"filter":[],"highlightAll":true,"version":true}'}
        }
        if timeFrom is not None and timeTo is not None:
            attributes['timeRestore'] = True
            attributes['timeTo'] = str(timeTo)
            attributes['timeFrom'] = str(timeFrom)
        uid, res = self.postKibanaSavedObject('dashboard',attributes)
        return uid, res

    def setup_kibana(self, index, timeField=None, searchCols=[], visCols=None, dashboard=True, timeFrom=None, timeTo=None, sets=True, ifexists='return_existing'):
        print(f'{index}: adding index-pattern')
        ipUID, _ipRes = self.addKibanaIndexPattern(index, timeField, ifexists=ifexists)
        if self.getKibanaConfig('defaultIndex') is None:
            # BUG the following is not really setting the defaultIndex as the Kibana UI see it...
            print(f'{index}: setting default index-pattern')
            self.addKibanaConfig('defaultIndex', ipUID)
        print(f'{index}: adding search')
        seUID, _seRes = self.addKibanaSearch(index+"-search", searchCols, ifexists=ifexists)
        visUIDs = []
        for i in visCols:
            if isinstance(i, str):
                i = HorizontalBar(i)
            print(f'{index}: adding visualisation for {i.field}')
            uid, _res = self.addVisualization(f'[{index}] {i.field}', i, ifexists=ifexists)
            visUIDs.append(uid)
        if dashboard:
            print(f'{index}: adding dashboard')
            daUID, _daRes = self.addDashboard(f'[{index}] Dashboard', seUID, visUIDs, timeFrom=timeFrom, timeTo=timeTo, ifexists=ifexists)
        if sets:
            print(f'{index}: setting time defaults')
            self.set_kibana_timeDefaults(timeFrom, timeTo)
        return {'index-pattern': ipUID, 'search': seUID, 'visualization': visUIDs, 'dashboard': daUID}

    def set_kibana_timeDefaults(self, timeFrom="now-15m", timeTo='now', mode='quick'):
        '''
        For accepted formats see https://www.elastic.co/guide/en/elasticsearch/reference/6.7/common-options.html#date-math
        '''
        # more configs on https://www.elastic.co/guide/en/kibana/current/advanced-options.html
        # maybe also set the timepicker:quickRanges key to a list of interesting time ranges.

        # value is a JSON, but as string.
        # btw we need to escape the outer {} in the f'...' string
        timeFrom = timeFrom or 'now-15m'
        timeTo = timeTo or 'now'
        value = { "from": str(timeFrom), "to": str(timeTo), "mode": "{mode}" }
        uid, res = self.addKibanaConfig("timepickerts", json.dumps(value))
        return uid, res
    def set_kibana_timeQuickRange(self, display, timeFrom, timeTo, section=3, id=None):
        '''
        For accepted formats see https://www.elastic.co/guide/en/elasticsearch/reference/6.7/common-options.html#date-math
        '''
        if id is None:
            result = requests.get(self.kibanaUrl('api/status'))
            result.raise_for_status()
            id = result.json()['version']['number']
        timeFrom = timeFrom or 'now-15m'
        timeTo = timeTo or 'now'
        value = [{"from": str(timeFrom), "to": str(timeTo), "display": display, "section": section}]
        uid, res = self.addKibanaConfig("timepicker:quickRanges", json.dumps(value), id=id)
        return uid, res
    def show_kibana_jupyter(self, height=500):
        # see e.g. https://github.com/tensorflow/tensorboard/blob/d9092143511cb04e4bfc904820305f1be45c67b3/tensorboard/notebook.py
        from IPython.display import IFrame
        url = self.kibanaUrl()
        iframe = IFrame(src=url, height=500, width="100%")
        return iframe

class Visualization(object):
    def __init__(self, field, agg='count'):
        self.field = field
        self.agg = agg
        self.visType = None
    def visState(self, title):
        visState = {
            'aggs':[
                {'id': '1', 'schema':'metric', 'type': self.agg},
                self.agg2(),
            ],
            'params': {
                'type': self.visType
            },
            'title': title,
            'type': self.visType,
        }
        return visState
    def agg2(self):
        raise NotImplementedError()
class HorizontalBar(Visualization):
    def __init__(self, field, size=20):
        super(HorizontalBar, self).__init__(field)
        self.visType = 'horizontal_bar'
        self.size = size
    def agg2(self):
        return {
                    'id': '2', 'schema':'segment', 'type': 'terms',
                    'params': {'field': self.field, 'size': self.size, 'order': 'desc', 'orderBy': '1',  }
                }
class TagCloud(HorizontalBar):
    def __init__(self, field, size=20):
        super(TagCloud, self).__init__(field, size)
        self.visType = 'tagcloud'
        self.params =  {
            "scale": "linear",
            "orientation": "single",
            "minFontSize": 18,
            "maxFontSize": 72,
            "showLabel": True
        }
class Histogram(Visualization):
    def __init__(self, field, interval):
        super(Histogram, self).__init__(field)
        self.visType = 'histogram'
        self.interval = interval
    def agg2(self):
        return {
            "id": "2",
            "enabled": True,
            "type": "histogram",
            "schema": "segment",
            "params": {
                "field": self.field,
                "interval": self.interval,
                "extended_bounds": {}
            }
        }
class DateHistogram(Visualization):
    def __init__(self, field):
        super(DateHistogram, self).__init__(field)
        self.visType = 'histogram'
    def agg2(self):
        return {
            "id": "2",
            "enabled": True,
            "type": "date_histogram",
            "schema": "segment",
            "params": {
                "field": self.field,
                "interval": "auto",
                "customInterval": "2h",
                "min_doc_count": 1,
                "extended_bounds": {}
            }
        }
