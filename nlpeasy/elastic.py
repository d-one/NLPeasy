# -*- coding: utf-8 -*-

"""Main module."""


from typing import Optional
import elasticsearch
from . import kibana
from . import docker

from .util import chunker, print_or_display, rm_nan_from_dict


def connect_elastic(
    docker_prefix: str = "nlp",
    start_on_docker: bool = True,
    host: str = "localhost",
    elastic_port: Optional[int] = None,
    kibana_port: Optional[int] = None,
    kibana_host: str = None,
    elk_version: str = "7.1.1",
    mount_volume_prefix: Optional[str] = None,
    verbose: bool = True,
    raise_error: bool = False,
    **kwargs,
) -> "ElasticStack":
    """Connect to running Elasticsearch and Kibana servers or start one on Docker.

    First this will try to connect to the specified host/ports.
    If no server can be reached then the docker is explored whether containers with name
    `{dockerPrefix}_elastic` and `{dockerPrefix}_kibana` are running and if found they are used.
    Else, such containers will be started.

    Parameters
    ----------
    docker_prefix :
        Docker containers for Elasticsearch and Kibana, and the docker network will be prefixed
        with this + '_' as is customary e.g. in docker-compose
    start_on_docker :
        If there is no reachable Elasticsearch server, should one be started on Docker (default: True)
    host :
        The host to try to connect to (default: 'localhost')
    elastic_port :
        The port on which try to connect to or start Elasticsearch on if not yet started.
        If ``None`` (default) then docker will find a port and the returned ELK will be using that.
    kibana_port :
        The port on which try to connect to or start Kibana on if not yet started.
        If ``None`` (default) then docker will find a port and the returned ELK will be using that.
    kibana_host :
        The host to try to connect to for Kibana.
        If ``None`` (default) the same as ``host``.
    elk_version :
        The version of the Elastic Stack to download if starting on Docker.
    mount_volume_prefix :
        If a docker container will be started this specifies where in the filesystem of the host
        the data should be saved. If ``None`` (default) data is not saved and will not survive
        restarts of the container.
    verbose :
        Should information be printed out.
    raise_error :
        Should there be an error raised.
    kwargs :
        Passed to :meth:`~nlpeasy.docker.start_elastic_on_docker`

    Returns
    -------
    ElasticStack
        The elastic stack found.
    """
    kibana_host = kibana_host or host
    elastic_port = elastic_port or 9200
    kibana_port = kibana_port or 5601
    log = print_or_display if verbose else lambda x: None
    elk = ElasticStack(
        host=host,
        elastic_port=elastic_port,
        kibana_port=kibana_port,
        kibana_host=kibana_host,
    )
    if elk.alive():
        log(f"Elasticsearch already running")
        # TODO warn if version mismatches elkVersion param
        log(elk)
        return elk
    if docker_prefix is None:
        if raise_error:
            raise RuntimeError(
                f"No running elasticsearch found on {host}:{elastic_port}."
            )
        else:
            log(f"No running elasticsearch found on {host}:{elastic_port}.")
            return None

    # Let's pass it on to docker:
    log(
        f"No elasticsearch on {host}:{elastic_port} found, "
        f"trying connect to docker container with prefix {docker_prefix}"
    )
    elk = docker.elastic_stack_from_docker(
        container_prefix=docker_prefix, set_as_default_elk=False
    )
    if elk is None or not elk.alive():
        if start_on_docker:
            log(f"No docker container with prefix {docker_prefix}; starting one")
            assert all(
                i not in kwargs for i in ["mountVolumePrefix", "version", "prefix"]
            )
            elk = docker.start_elastic_on_docker(
                prefix=docker_prefix,
                elk_version=elk_version,
                mount_volume_prefix=mount_volume_prefix,
                **kwargs,
            )
        else:
            msg = (
                f"No running elasticsearch found on docker with prefix {docker_prefix}."
            )
            if raise_error:
                raise RuntimeError(msg)
            else:
                log(msg)
                return None
    log(elk)
    return elk


class ElasticStack(object):
    def __init__(
        self,
        host="localhost",
        elastic_port=9200,
        kibana_port=5601,
        protocol="http",
        kibana_host=None,
        kibana_protocol=None,
        verify_certs=True,
        set_as_default_stack=True,
        **kwargs,
    ):
        self._host = host
        self._elasticPort = elastic_port
        self._protocol = protocol
        self._verify_certs = verify_certs

        self._es = None
        self._kibana = None
        self._elasticKwargs = kwargs

        self.kibana = kibana.Kibana(
            host=self._host if kibana_host is None else kibana_host,
            port=kibana_port,
            protocol=self._protocol if kibana_protocol is None else kibana_protocol,
            verify_certs=self._verify_certs,
        )

        if set_as_default_stack:
            set_default_elk(self)

    def alive(self, verbose=True):
        import logging

        urllib_logger = logging.getLogger("request")
        orig_max_retries = 3
        orig_level = urllib_logger.level
        result = False
        try:
            # BUG Disabling logging does not work:
            urllib_logger.setLevel(logging.FATAL)
            orig_max_retries = self.es.transport.max_retries
            self.es.transport.max_retries = 0
            result = self.es.ping() and self.kibana.alive()
        except Exception as e:
            if verbose:
                print(e)
        self.es.transport.max_retries = orig_max_retries
        urllib_logger.setLevel(orig_level)
        return result

    def wait_for(
        self,
        timeout: float = 10,
        interval: float = 0.5,
        raise_error=False,
        verbose=False,
    ) -> bool:
        from datetime import datetime
        from time import sleep

        start = datetime.now()
        while timeout <= 0 or (datetime.now() - start).seconds < timeout:
            if self.alive(verbose=verbose):
                return True
            sleep(interval)
        if raise_error:
            raise RuntimeError("")
        return False

    def url(self):
        return f"{self._protocol}://{self._host}:{self._elasticPort}"

    def __repr__(self):
        return f"ElasticSearch on {self.url()}\n" + self.kibana.__repr__()

    def _repr_html_(self):
        return (
            f"ElasticSearch on <a href='{self.url()}'>{self.url()}</a> <br> "
            + self.kibana._repr_html_()
        )

    @property
    def es(self):
        if self._es is None:
            host = {
                "host": self._host,
                "port": self._elasticPort,
                "use_ssl": self._protocol == "https",
            }
            self._es = elasticsearch.Elasticsearch(
                [host], verify_certs=self._verify_certs, **self._elasticKwargs
            )
        return self._es

    def get_analysis(self, lang="english", synonyms=None):
        filter_names = []
        if lang == "english":
            filter_names.append("english_possessive_stemmer")
        filter_names.append("lowercase")
        filters = {
            f"{lang}_stop": {"type": "stop", "stopwords": f"_{lang}_"},
            f"{lang}_stemmer": {"type": "stemmer", "language": f"{lang}"},
        }
        filter_names.extend(filters.keys())
        if lang == "english":
            filters["english_possessive_stemmer"] = {
                "type": "stemmer",
                "language": "possessive_english",
            }
        if synonyms is not None:
            filters[f"{lang}_synonym"] = {
                "type": "synonym",
                "synonyms": synonyms
                # "synonyms_path": "analysis/synonym.txt"
            }
            filter_names.append(f"{lang}_synonym")

        analyzer = {f"{lang}_syn": {"tokenizer": "standard", "filter": filter_names}}
        return filters, analyzer

    # TODO languages, synonyms,
    def create_index(
        self,
        index="texts",
        doctype="_doc",
        create=True,
        text_cols=[],
        tag_cols=[],
        geopoint_cols=[],
        synonyms=[],
        lang="english",
        delete_old=True,
        verbose=False,
    ):
        # assert lang == 'english'
        properties = {}
        for k in text_cols:
            # TODO Make sure that the analyzer is created as f"{lang}_syn":
            properties[k] = {
                "type": "text",
                "fielddata": True,
                "analyzer": f"{lang}_syn",
            }
        for k in tag_cols:
            properties[k] = {"type": "keyword"}
        for k in geopoint_cols:
            properties[k] = {"type": "geo_point"}
        properties["suggest"] = {"type": "completion"}
        mapping = {
            # "_timestamp": {"enabled": "false"},
            "properties": properties
        }
        if self.es.info()["version"]["number"] < "7":
            mapping = {doctype: mapping}
        if create:
            filters, analyzer = self.get_analysis(lang, synonyms)
            body = {
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
                "mappings": mapping,
            }
            if verbose:
                print(body)
            if delete_old:
                try:
                    self.es.indices.delete(index)
                except:  # noqa: E722
                    pass
            self.es.indices.create(index=index, body=body)  # , ignore=[]
            return body
        else:
            self.es.indices.put_mapping(index=index, doc_type=doctype, body=mapping)

    def load_docs(
        self,
        index,
        texts,
        doctype="_doc",
        delete_old=False,
        chunksize=1000,
        id_col=None,
        suggest_col=None,
        progbar=True,
    ):
        if id_col is None:
            id_col = texts.index
        if delete_old:
            try:
                self.es.indices.delete(index)
            except:  # noqa: E722
                pass
        # createIndex(index=index, create=deleteOld)

        for ic, cdf in enumerate(chunker(texts, chunksize, progbar=progbar)):
            docs = cdf.to_dict(orient="records")
            for ii, doc in enumerate(docs):
                i = ic * chunksize + ii
                doc = rm_nan_from_dict(doc)
                if suggest_col and suggest_col in doc:
                    doc["suggest"] = doc[suggest_col]
                try:
                    self.es.index(index=index, doc_type=doctype, id=id_col[i], body=doc)
                except elasticsearch.ElasticsearchException as ex:
                    print(ex)
                    print(doc)
                    print("=" * 80)

    def truncate(self, index, doctype="text"):
        self._es.delete_by_query(index, {"query": {"match_all": {}}})

    def show_kibana(self, how=None, *args, **kwargs):
        """Opens the Kibana UI either by opening it in the default webbrowser or by showing the URL.

        Parameters
        ----------
        how :
            One or more of ``'print'``, ``'webbrowser'``, or ``'jupyter'``
        args :
            passed to :meth:`~nlpeasy.kibana.Kibana.kibanaUrl`
        kwargs
            passed to :meth:`~nlpeasy.kibana.Kibana.kibanaUrl`

        Returns
        -------
        If ``how`` contains ``'jupyter'`` then the IPython display HTML with a link.
        """
        self.kibana.show_kibana(how=how, *args, **kwargs)


__DEFAULT_STACK = None


def default_stack():
    global __DEFAULT_STACK
    if __DEFAULT_STACK is None:
        __DEFAULT_STACK = ElasticStack()
    return __DEFAULT_STACK


def set_default_elk(es):
    global __DEFAULT_STACK
    __DEFAULT_STACK = es
