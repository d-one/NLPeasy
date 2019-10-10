# -*- coding: utf-8 -*-

"""Main module."""
# TODO maybe rename this module to docker_util so we are distinct from the docker-py we use?


import glob
from pathlib import Path
import pandas as pd

from . import elastic

try:
    import docker as dockerpy
except ImportError as identifier:
    raise Exception('Please instell the python docker package for start_elastic_on_docker to work: pip install docker')

def start_elastic_on_docker(prefix, errorIfExists=False,
                            elkVersion='latest', elasticPassword='nlp is fun',
                            mountVolumePrefix=Path('./elastic-data/'), mountType='bind', mkdir=True,
                            kibanaPluginDirectory=None,
                            elasticPort=None, kibanaPort=None,
                            client=dockerpy.from_env(), forcePull=False, rm=True,
                            setAsDefaultElasticStack=True):
    """
    stack = start_elastic_on_docker('mynlpstack', version='6.3.2')
    """
    assert kibanaPluginDirectory is None

    el_im, ki_im = [ f"docker.elastic.co/{i}/{i}-oss:{elkVersion}" for i in ['elasticsearch','kibana'] ]
    if forcePull:
        client.images.pull(el_im)
        client.images.pull(ki_im)
    network = f'{prefix}_network'
    if not len(client.networks.list(names=[network])):
        client.networks.create(network)


    el_name = prefix+"_elastic"
    el_ulimits = [dockerpy.types.Ulimit(name='memlock', soft=-1, hard=-1), dockerpy.types.Ulimit(name='nofile', soft=65536, hard=65536)]
    el_env = [f'ELASTIC_PASSWORD={elasticPassword}','discovery.type=single-node',
             'cluster.name=docker-cluster','bootstrap.memory_lock=true','"ES_JAVA_OPTS=-Xms512m -Xmx512m"']
    if mountVolumePrefix is not None:
        p = Path(mountVolumePrefix)
        if not p.exists():
            if mkdir:
                p.mkdir(parents=False, exist_ok=False)
            else:
                raise FileNotFoundError(p)
        el_p = (p / 'elastic-data').absolute()
        ki_p = (p / 'kibana-plugins').absolute()
        el_p.mkdir(exist_ok=True)
        ki_p.mkdir(exist_ok=True)
        print(el_p, ki_p)
        el_mnts = [ dockerpy.types.Mount('/usr/share/elasticsearch/data', str(el_p), type=mountType ) ]
        ki_mnts = [ dockerpy.types.Mount('/usr/share/kibana/plugins', str(ki_p), type=mountType ) ]
    else:
        el_mnts, ki_mnts = [],[]
    if errorIfExists or not len(client.containers.list(filters={'name': el_name})):
        client.containers.run(el_im, name=el_name, detach=True, remove=rm, network=network, ports={'9200': elasticPort},
                environment=el_env, mounts=el_mnts, ulimits=el_ulimits)
    elasticPort = client.api.inspect_container(el_name)['NetworkSettings']['Ports']['9200/tcp'][0]['HostPort']

    ki_name = prefix+"_kibana"
    ki_env = [f'ELASTIC_PASSWORD={elasticPassword}',
             'SERVER_NAME=kibana', f'ELASTICSEARCH_URL=http://{el_name}:9200', f'ELASTICSEARCH_HOSTS=http://{el_name}:9200']
    if errorIfExists or not len(client.containers.list(filters={'name': ki_name})):
        client.containers.run(ki_im, name=ki_name, detach=True, remove=rm, network=network, ports={'5601': kibanaPort},
                environment=ki_env, mounts=ki_mnts)
    kibanaPort = client.api.inspect_container(ki_name)['NetworkSettings']['Ports']['5601/tcp'][0]['HostPort']

    elk = None
    # TODO find docker containers IP
    elk = elastic.ElasticStack(elasticPort=elasticPort, kibanaPort=kibanaPort)
    if setAsDefaultElasticStack:
        elastic.setDefaultStack(elk)

    return elk

def container_running(name, client=dockerpy.from_env(), raiseRuntimeError=None):
    c = [ _ for _ in client.containers.list(filters={'name': name}) if _.name == name ]
    if len(c) == 1 and c[0].status == 'running':
        return True
    if raiseRuntimeError:
        msg = raiseRuntimeError if isinstance(raiseRuntimeError, str) else f'container {name} not running'
        raise RuntimeError(msg)

def elasticStackFromDocker(containerPrefix, setAsDefaultStack=True, raiseRuntimeError=False):
    el_name, ki_name = containerPrefix+"_elastic", containerPrefix+"_kibana"
    client = dockerpy.from_env()
    if not container_running(el_name, client=client, raiseRuntimeError=raiseRuntimeError):
        return None
    elasticPort = client.api.inspect_container(el_name)['NetworkSettings']['Ports']['9200/tcp'][0]['HostPort']
    kibanaPort = client.api.inspect_container(ki_name)['NetworkSettings']['Ports']['5601/tcp'][0]['HostPort']
    from . import elastic
    es = elastic.ElasticStack(elasticPort=elasticPort, kibanaPort=kibanaPort)
    if setAsDefaultStack:
        elastic.setDefaultStack(es)
    return es


def stop_elastic_on_docker(containerPrefix):
    client = dockerpy.from_env()
    for c in client.containers.list(filters={'name': containerPrefix+'_'}):
        c.stop()
    network = f'{containerPrefix}_network'
    for n in client.networks.list(names=[network]):
        n.remove()

