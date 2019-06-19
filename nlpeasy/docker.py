# -*- coding: utf-8 -*-

"""Main module."""


import glob
from pathlib import Path
import pandas as pd

try:
    import docker
except ImportError as identifier:
    raise Exception('Please instell the python docker package for start_elastic_on_docker to work: pip install docker')

def start_elastic_on_docker(prefix, errorIfExists=False,
                            version='latest', elasticPassword='nlp is fun',
                            mountVolumePrefix=Path('./elastic-data/'), mountType='bind',
                            kibanaPluginDirectory=None,
                            elasticPort=None, kibanaPort=None,
                            client=docker.from_env(), forcePull=False, rm=True,
                            setAsDefaultElasticStack=True):
    """
    stack = start_elastic_on_docker('mynlpstack', version='6.3.2')
    """
    assert kibanaPluginDirectory is None

    el_im, ki_im = [ f"docker.elastic.co/{i}/{i}-oss:{version}" for i in ['elasticsearch','kibana'] ]
    if forcePull:
        client.images.pull(el_im)
        client.images.pull(ki_im)
    network = f'{prefix}_network'
    if not len(client.networks.list(names=[network])):
        client.networks.create(network)
    
    
    el_name = prefix+"_elastic"
    el_ulimits = [docker.types.Ulimit(name='memlock', soft=-1, hard=-1), docker.types.Ulimit(name='nofile', soft=65536, hard=65536)]
    el_env = [f'ELASTIC_PASSWORD={elasticPassword}','discovery.type=single-node',
             'cluster.name=docker-cluster','bootstrap.memory_lock=true','"ES_JAVA_OPTS=-Xms512m -Xmx512m"']
    if mountVolumePrefix is not None:
        p = Path(mountVolumePrefix)
        if not p.exists():
            raise FileNotFoundError(p)
        el_p = (p / 'elastic-data').absolute()
        ki_p = (p / 'kibana-plugins').absolute()
        el_p.mkdir(exist_ok=True)
        ki_p.mkdir(exist_ok=True)
        print(el_p, ki_p)
        el_mnts = [ docker.types.Mount('/usr/share/elasticsearch/data', str(el_p), type=mountType ) ]
        ki_mnts = [ docker.types.Mount('/usr/share/kibana/plugins', str(ki_p), type=mountType ) ]
    else:
        el_mnts, ki_mnts = [],[]
    if errorIfExists or not len(client.containers.list(filters={'name': el_name})):
        client.containers.run(el_im, name=el_name, detach=True, remove=rm, network=network, ports={'9200': elasticPort},
                environment=el_env, mounts=el_mnts, ulimits=el_ulimits)
    elasticPort = client.api.inspect_container(el_name)['NetworkSettings']['Ports']['9200/tcp'][0]['HostPort']

    ki_name = prefix+"_kibana"
    ki_env = [f'ELASTIC_PASSWORD={elasticPassword}',
             'SERVER_NAME: kibana', f'ELASTICSEARCH_URL=http://{el_name}:9200', f'ELASTICSEARCH_HOSTS=http://{el_name}:9200']
    if errorIfExists or not len(client.containers.list(filters={'name': ki_name})):
        client.containers.run(ki_im, name=ki_name, detach=True, remove=rm, network=network, ports={'5601': kibanaPort},
                environment=ki_env, mounts=ki_mnts)
    kibanaPort = client.api.inspect_container(ki_name)['NetworkSettings']['Ports']['5601/tcp'][0]['HostPort']
    
    es = None
    if setAsDefaultElasticStack:
        from . import elastic
        es = elastic.ElasticStack(elasticPort=elasticPort, kibanaPort=kibanaPort)
        elastic.setDefaultStack(es)

    return (es, el_name, ki_name, network)

def elasticStackFromDocker(containerPrefix, setAsDefaultStack=True):
    el_name, ki_name = containerPrefix+"_elastic", containerPrefix+"_kibana"
    client = docker.from_env()
    elasticPort = client.api.inspect_container(el_name)['NetworkSettings']['Ports']['9200/tcp'][0]['HostPort']
    kibanaPort = client.api.inspect_container(ki_name)['NetworkSettings']['Ports']['5601/tcp'][0]['HostPort']
    from . import elastic
    es = elastic.ElasticStack(elasticPort=elasticPort, kibanaPort=kibanaPort)
    if setAsDefaultStack:
        elastic.setDefaultStack(es)
    return es


def stop_elastic_on_docker(containerPrefix):
    client = docker.from_env()
    for c in client.containers.list(filters={'name': containerPrefix+'_'}):
        c.stop()
    network = f'{containerPrefix}_network'
    for n in client.networks.list(names=[network]):
        n.remove()

