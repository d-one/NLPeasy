import os

from jupyter_server_proxy.handlers import ProxyHandler
from notebook.notebookapp import NotebookApp


def setup_jupyter_kibana():
    """
    Proxy /kibana to an already running server on localhost:5601.
    This configuration is used by the jupyter-server-proxy package to setup the mapping.
    NLPeasy however will then monkey-patch that by substituting a different
    ProxyHandler implementation.
    """
    return {
        "command": None,  # connect to the running server - by our changed jupyter_server_proxy
        "launcher_entry": {
            "title": "Kibana",
            "icon_path": os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "icons", "kibana.svg"
            ),
        },
        "absolute_url": False,
        "port": 5601,
        "new_browser_tab": False,
    }


def _jupyter_server_extension_paths():
    return [{"module": "nlpeasy.jupyter_proxy_kibana",}]


_kibana_routing_rule = None


def load_jupyter_server_extension(nbapp: NotebookApp):
    # for the following we actually need that jupyter-server-proxy's load_jupyter_server_extension
    # already has run - fortunately in alphabetical order jupyter comes before nlp ;-)

    rules = nbapp.web_app.default_router.rules

    for r1 in rules:
        for r in r1.target.rules:
            if r.matcher.regex.pattern.startswith("/kibana/"):
                global _kibana_routing_rule
                r.target = LocalProxyPortHandler  # <class 'jupyter_server_proxy.config._make_serverproxy_handler.<locals>._Proxy'>
                r.target_kwargs = {
                    "absolute_url": False,
                    "port": 5601,
                }
                _kibana_routing_rule = r


class LocalProxyPortHandler(ProxyHandler):
    """
    A tornado request handler that proxies HTTP and websockets
    from a port on the local system. Same as the above ProxyHandler,
    but specific to 'localhost'.
    """

    def __init__(self, *args, **kwargs: dict):
        self.port = kwargs.pop("port", False)
        super().__init__(*args, **kwargs)

    async def http_get(self, proxied_path):
        return await self.proxy(proxied_path)

    def proxy_request_options(self):
        """A dictionary of options to be used when constructing
        a tornado.httpclient.HTTPRequest instance for the proxy request."""
        opts = super().proxy_request_options()
        opts["allow_nonstandard_methods"] = True
        return opts

    async def open(self, proxied_path):
        return await self.proxy_open("localhost", self.port, proxied_path)

    def post(self, proxied_path):
        return self.proxy(proxied_path)

    def put(self, proxied_path):
        return self.proxy(proxied_path)

    def delete(self, proxied_path):
        return self.proxy(proxied_path)

    def head(self, proxied_path):
        return self.proxy(proxied_path)

    def patch(self, proxied_path):
        return self.proxy(proxied_path)

    def options(self, proxied_path):
        return self.proxy(proxied_path)

    def proxy(self, proxied_path):
        # self.log.debug(f"Proxying to localhost : {self.port} /{proxied_path} .")
        return super().proxy("localhost", self.port, "/" + proxied_path)
