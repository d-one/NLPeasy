# -*- coding: utf-8 -*-

"""Kibana module."""


import requests
import json
from . import util

from typing import Optional, Sequence, Union


class Kibana(object):
    def __init__(
        self, host="localhost", port=5601, protocol="http", verify_certs=True, **kwargs
    ):
        self._host = host
        self._port = port
        self._protocol = protocol
        self._verify_certs = verify_certs
        self._defaultIndexPatternUID = None
        self._defaultSearchUID = None
        self._kibana_version = None

    def kibana_url(self, path=""):
        # TODO maybe URLEncode path?
        if path and path[0] != "/":
            # TODO Warn about missing initial '/'?
            path = "/" + path
        return f"{self._protocol}://{self._host}:{self._port}{path}"

    def alive(self, verbose=True):
        resp = requests.head(self.kibana_url("api/status"))
        return resp.status_code == 200

    def show_kibana(
        self, how: Optional[Union[str, Sequence[str]]] = None, *args, **kwargs
    ) -> Optional["HTML"]:
        """Opens the Kibana UI either by opening it in the default webbrowser or by showing the URL.

        Parameters
        ----------
        how :
            One or more of ``'print'``, ``'webbrowser'``, or ``'jupyter'``
        args :
            passed to Kibana.kibanaUrl
        kwargs
            passed to Kibana.kibanaUrl

        Returns
        -------
        If ``how`` contains ``'jupyter'`` then the IPython display HTML with a link.
        """
        if how is None:
            how = "jupyter" if util.IS_JUPYTER else "webbrowser"
            # TODO can we figure out "non-interactive" to put how='print' then?
        how = how if isinstance(how, list) else [how]
        url = self.kibana_url(*args, **kwargs)
        if "print" in how:
            print(f"Open: {url}")
        if "webbrowser" in how:
            import webbrowser

            webbrowser.open(url)
        if "jupyter" in how or "ipython" in how:
            from IPython.core.display import HTML

            return HTML(self._repr_html_())

    def __repr__(self):
        return f"Kibana on {self.kibana_url()}"

    def _repr_html_(self):
        return f"Kibana on <a href='{self.kibana_url()}'>{self.kibana_url()}</a>"

    def get_kibana_saved_objects(self, type="index-pattern", search=None, fields=None):
        type = "&type=" + type if type else ""
        search = "&search=" + search if search else ""
        fields = "&fields=" + fields if fields else ""
        resp = requests.get(
            self.kibana_url(f"/api/saved_objects/_find?{type}{search}{fields}")
        )
        resp.raise_for_status()
        result = resp.json()["saved_objects"]
        return result

    def post_kibana_saved_object(self, type, attributes, id=None):
        body = {"attributes": attributes}
        id = "/" + id if id else ""
        result = requests.post(
            self.kibana_url(f"/api/saved_objects/{type}{id}?overwrite=true"),
            headers={"kbn-xsrf": "true"},
            json=body,
        )
        result.raise_for_status()
        # return result.json()
        return result.json()["id"], result.json()

    def update_kibana_saved_object(self, type, attributes, id):
        body = {"attributes": attributes}
        assert isinstance(id, str) and len(id) > 0
        id = "/" + id
        result = requests.put(
            self.kibana_url(f"/api/saved_objects/{type}{id}"),
            headers={"kbn-xsrf": "true"},
            json=body,
        )
        result.raise_for_status()
        # return result.json()
        return result.json()["id"], result.json()

    def delete_kibana_saved_object(self, type, uid):
        u = self.kibana_url(f"/api/saved_objects/{type}/{uid}")
        resp = requests.delete(u, headers={"kbn-xsrf": "true"})
        resp.raise_for_status
        print(resp.json())
        return resp.json()

    def truncate_kibana_saved_objects(
        self,
        types=["dashboard", "visualization", "search", "index-pattern"],
        search=None,
    ):
        for t in types:
            if search is not None and t == "index-pattern_________":
                continue
            objs = self.get_kibana_saved_objects(type=t, fields="name", search=search)
            print(f"deleting {len(objs)} objects of type {t}...")
            for i in objs:
                # print(i['id'])
                self.delete_kibana_saved_object(t, i["id"])
        print("finished deleting")

    def get_kibana_config(
        self, name=None, only_last_set_value=True, default_value=None
    ):
        assert only_last_set_value
        config = self.get_kibana_saved_objects("config")
        # TODO need to implement for onlyLastSetValue=False as well or warn if multiple values?
        result = dict()
        for i in config:
            c = i["attributes"]
            result.update(c)
        if name is not None:
            if name in result:
                return result[name]
            else:
                return default_value
        return result

    def get_saved_object_if_exists(self, type, title, ifexists):
        for i in self.get_kibana_saved_objects(type, title, "title"):
            if i["attributes"]["title"] == title:
                # it exists already
                if ifexists == "return_existing":
                    print(f"reusing {type} {title}")
                    return i["id"], None
                if ifexists == "error":
                    raise ValueError(f"{type} {title} already exists!")
                if ifexists == "overwrite":
                    self.delete_kibana_saved_object(type, i["id"])
                if ifexists != "add":
                    raise ValueError(f"ifexists={ifexists} not understood!!")
        return False

    def set_kibana_config(self, name, value, add_to_list=False, id=None):
        assert not add_to_list
        if id is None:
            id = self.kibana_version()
        # Workaround? Get Saved object for settings first, so it is instantiated:
        existing = self.get_kibana_config(name=id)
        attributes = {name: value}
        if existing is not None:
            res = self.update_kibana_saved_object("config", attributes, id=id)
        else:
            res = self.post_kibana_saved_object("config", attributes, id=id)
        return res

    def add_kibana_index_pattern(
        self,
        index_pattern,
        time_field=None,
        set_default_index_pattern=True,
        ifexists="return_existing",
    ):
        uid = self.get_saved_object_if_exists("index-pattern", index_pattern, ifexists)
        if uid:
            return uid, None
        attributes = {
            "title": index_pattern,
        }
        if time_field is not None:
            attributes["timeFieldName"] = time_field
        uid, result = self.post_kibana_saved_object("index-pattern", attributes)
        if set_default_index_pattern:
            self._defaultIndexPatternUID = uid

        return uid, result

    def add_kibana_search(
        self,
        title,
        columns,
        description=None,
        sort=None,
        set_default_search=True,
        index_pattern_uid=None,
        ifexists="return_existing",
    ):
        if index_pattern_uid is None:
            index_pattern_uid = self._defaultIndexPatternUID
        uid = self.get_saved_object_if_exists("search", title, ifexists)
        if uid:
            return uid, None
        search_source_json = {
            "index": index_pattern_uid,
            "highlightAll": True,
            # "version": True,
            "query": {"query": "", "language": "kuery"},
            "filter": [],
        }
        attributes = {
            "title": title,
            "columns": columns,
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps(search_source_json)
            },
        }
        if description is not None:
            attributes["description"] = description
        if sort is not None:
            attributes["sort"] = sort
        uid, res = self.post_kibana_saved_object(type="search", attributes=attributes)
        if set_default_search:
            self._defaultSearchUID = uid
        return uid, res

    def add_visualization(
        self, title, viz, index_pattern_uid=None, ifexists="return_existing"
    ):
        if index_pattern_uid is None:
            index_pattern_uid = self._defaultIndexPatternUID
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
        uid = self.get_saved_object_if_exists("visualization", title, ifexists)
        if uid:
            return uid, None
        vis_state = viz.vis_state(title)
        search_source_json = {
            "index": index_pattern_uid,
            "filter": [],
            "query": {"language": "kuery", "query": ""},
        }
        uid, res = self.post_kibana_saved_object(
            "visualization",
            attributes={
                "title": title,
                "visState": json.dumps(vis_state),
                "uiStateJSON": '{"vis":{"legendOpen":false}}',
                "kibanaSavedObjectMeta": {
                    "searchSourceJSON": json.dumps(search_source_json)
                },
            },
        )
        return uid, res

    def add_dashboard(
        self,
        title,
        search_uid,
        vis_uids,
        time_from=None,
        time_to=None,
        n_vis_cols=3,
        vis_w=16,
        vis_h=16,
        search_w=48,
        search_h=16,
        ifexists="return_existing",
    ):
        uid = self.get_saved_object_if_exists("dashboard", title, ifexists)
        if uid:
            return uid, None
        panels = [
            {
                "panelIndex": "1",
                "gridData": {"x": 0, "y": 0, "w": search_w, "h": search_h, "i": "1"},
                "version": "6.3.2",
                "type": "search",
                "id": search_uid,
                "embeddableConfig": {},
            }
        ]
        for i, v in enumerate(vis_uids):
            ix, iy = i % n_vis_cols, i // n_vis_cols
            x, y = ix * vis_w, search_h + iy * vis_h
            # print(ix,iy, x,y)
            i_str = str(i + 2)
            panels.append(
                {
                    "panelIndex": i_str,
                    "gridData": {"x": x, "y": y, "w": vis_w, "h": vis_h, "i": i_str},
                    "version": "6.3.2",
                    "type": "visualization",
                    "id": v,
                    "embeddableConfig": {},
                }
            )
        attributes = {
            "title": title,
            #      'hits': 0,
            "description": "",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": '{"darkTheme":false,"useMargins":true,"hidePanelTitles":false}',
            #      'version': 1,
            #      'refreshInterval': {'display': 'Off', 'pause': False, 'value': 0},
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": '{"query":{"query":"","language":"kuery"},"filter":[],"highlightAll":true,"version":true}'  # noqa: E501
            },
        }
        if time_from is not None and time_to is not None:
            attributes["timeRestore"] = True
            attributes["timeTo"] = str(time_to)
            attributes["timeFrom"] = str(time_from)
        uid, res = self.post_kibana_saved_object("dashboard", attributes)
        return uid, res

    def setup_kibana(
        self,
        index,
        time_field=None,
        search_cols=[],
        vis_cols=None,
        dashboard=True,
        time_from=None,
        time_to=None,
        sets=True,
        ifexists="return_existing",
    ):
        print(f"{index}: adding index-pattern")
        ip_uid, _ip_res = self.add_kibana_index_pattern(
            index, time_field, ifexists=ifexists
        )
        if self.get_kibana_config("defaultIndex") is None:
            # BUG the following is not really setting the defaultIndex as the Kibana UI see it...
            print(f"{index}: setting default index-pattern")
            self.set_kibana_config("defaultIndex", ip_uid)
        print(f"{index}: adding search")
        se_uid, _se_res = self.add_kibana_search(
            index + "-search", search_cols, ifexists=ifexists
        )
        vis_uids = []
        for i in vis_cols:
            if isinstance(i, str):
                i = HorizontalBar(i)
            print(f"{index}: adding visualisation for {i.field}")
            uid, _res = self.add_visualization(
                f"[{index}] {i.field}", i, ifexists=ifexists
            )
            vis_uids.append(uid)
        if dashboard:
            print(f"{index}: adding dashboard")
            da_uid, _da_res = self.add_dashboard(
                f"[{index}] Dashboard",
                se_uid,
                vis_uids,
                time_from=time_from,
                time_to=time_to,
                ifexists=ifexists,
            )
        if sets:
            print(f"{index}: setting time defaults")
            self.set_kibana_time_defaults(time_from, time_to)
        return {
            "index-pattern": ip_uid,
            "search": se_uid,
            "visualization": vis_uids,
            "dashboard": da_uid,
        }

    def set_kibana_time_defaults(
        self, time_from="now-15m", time_to="now", mode="quick"
    ):
        """
        For accepted formats
        see https://www.elastic.co/guide/en/elasticsearch/reference/6.7/common-options.html#date-math
        """
        # more configs on https://www.elastic.co/guide/en/kibana/current/advanced-options.html
        # maybe also set the timepicker:quickRanges key to a list of interesting time ranges.

        # value is a JSON, but as string.
        # btw we need to escape the outer {} in the f'...' string
        time_from = time_from or "now-15m"
        time_to = time_to or "now"
        value = {"from": str(time_from), "to": str(time_to), "mode": "{mode}"}
        configname = (
            "timepicker:timeDefaults"
            if self.kibana_version() >= "7"
            else "timepickerts"
        )
        uid, res = self.set_kibana_config(configname, json.dumps(value))
        return uid, res

    def set_kibana_time_quick_range(
        self, display, time_from, time_to, section=3, id=None
    ):
        """
        For accepted formats see
        https://www.elastic.co/guide/en/elasticsearch/reference/6.7/common-options.html#date-math
        """
        if id is None:
            id = self.kibana_version()
        time_from = time_from or "now-15m"
        time_to = time_to or "now"
        value = [
            {
                "from": str(time_from),
                "to": str(time_to),
                "display": display,
                "section": section,
            }
        ]
        uid, res = self.set_kibana_config(
            "timepicker:quickRanges", json.dumps(value), id=id
        )
        return uid, res

    def kibana_version(self):
        if not self._kibana_version:
            result = requests.get(self.kibana_url("api/status"))
            result.raise_for_status()
            self._kibana_version = result.json()["version"]["number"]
        return self._kibana_version

    def show_kibana_jupyter(self, height=500):
        # see e.g.
        # https://github.com/tensorflow/tensorboard/blob/d9092143511cb04e4bfc904820305f1be45c67b3/tensorboard/notebook.py
        from IPython.display import IFrame

        url = self.kibana_url()
        iframe = IFrame(src=url, height=500, width="100%")
        return iframe


class Visualization(object):
    def __init__(self, field, agg="count"):
        self.field = field
        self.agg = agg
        self.visType = None

    def vis_state(self, title):
        vis_state = {
            "aggs": [
                {"id": "1", "schema": "metric", "type": self.agg},
                self.agg2(),
            ],  # noqa: E231
            "params": {"type": self.visType},
            "title": title,
            "type": self.visType,
        }
        return vis_state

    def agg2(self):
        raise NotImplementedError()


class HorizontalBar(Visualization):
    def __init__(self, field, size=20):
        super(HorizontalBar, self).__init__(field)
        self.visType = "horizontal_bar"
        self.size = size

    def agg2(self):
        return {
            "id": "2",
            "schema": "segment",
            "type": "terms",
            "params": {
                "field": self.field,
                "size": self.size,
                "order": "desc",
                "orderBy": "1",
            },
        }


class TagCloud(HorizontalBar):
    def __init__(self, field, size=20):
        super(TagCloud, self).__init__(field, size)
        self.visType = "tagcloud"
        self.params = {
            "scale": "linear",
            "orientation": "single",
            "minFontSize": 18,
            "maxFontSize": 72,
            "showLabel": True,
        }


class Histogram(Visualization):
    def __init__(self, field, interval):
        super(Histogram, self).__init__(field)
        self.visType = "histogram"
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
                "extended_bounds": {},
            },
        }


class DateHistogram(Visualization):
    def __init__(self, field):
        super(DateHistogram, self).__init__(field)
        self.visType = "histogram"

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
                "extended_bounds": {},
            },
        }
