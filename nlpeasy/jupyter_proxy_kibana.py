import os

def setup_jupyter_kibana():
    '''Proxy /kibana to an already running server on localhost:5601.'''
    name = 'kibana'
    return {
        'command': None,    # connect to the running server - by our changed jupyter_server_proxy
        'launcher_entry': {
            'title': 'Kibana',
            'icon_path': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'kibana.svg')
        },
        "absolute_url": False,
        "port": 5601,
        "new_browser_tab": False,
    }
