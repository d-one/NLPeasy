# -*- coding: utf-8 -*-

"""Main module."""
# TODO maybe rename this module to docker_util so we are distinct from the docker-py we use?


from pathlib import Path

from . import elastic

try:
    import docker as dockerpy
except ImportError:
    raise Exception(
        "Please instell the python docker package for start_elastic_on_docker to work: pip install docker"
    )


def start_elastic_on_docker(
    prefix,
    error_if_exists=False,
    elk_version="latest",
    elastic_password="nlp is fun",
    mount_volume_prefix=Path("./elastic-data/"),
    mount_type="bind",
    mkdir=True,
    kibana_plugin_directory=None,
    elastic_port=None,
    kibana_port=None,
    client=dockerpy.from_env(),
    force_pull=False,
    rm=True,
    set_as_default_elk=True,
):
    """
    >>> stack = start_elastic_on_docker('mynlpstack', version='6.3.2')
    """
    assert kibana_plugin_directory is None

    el_im, ki_im = [
        f"docker.elastic.co/{i}/{i}-oss:{elk_version}"
        for i in ["elasticsearch", "kibana"]
    ]
    if force_pull:
        client.images.pull(el_im)
        client.images.pull(ki_im)
    network = f"{prefix}_network"
    network_obj = get_network(network)  # noqa: F841

    el_name = prefix + "_elastic"
    el_ulimits = [
        dockerpy.types.Ulimit(name="memlock", soft=-1, hard=-1),
        dockerpy.types.Ulimit(name="nofile", soft=65536, hard=65536),
    ]
    el_env = [
        f"ELASTIC_PASSWORD={elastic_password}",
        "discovery.type=single-node",
        "cluster.name=docker-cluster",
        "bootstrap.memory_lock=true",
        '"ES_JAVA_OPTS=-Xms512m -Xmx512m"',
    ]
    if mount_volume_prefix is not None:
        p = Path(mount_volume_prefix)
        if not p.exists():
            if mkdir:
                p.mkdir(parents=False, exist_ok=False)
            else:
                raise FileNotFoundError(p)
        el_p = (p / "elastic-data").absolute()
        ki_p = (p / "kibana-plugins").absolute()
        el_p.mkdir(exist_ok=True)
        ki_p.mkdir(exist_ok=True)
        print(el_p, ki_p)
        el_mnts = [
            dockerpy.types.Mount(
                "/usr/share/elasticsearch/data", str(el_p), type=mount_type
            )
        ]
        ki_mnts = [
            dockerpy.types.Mount(
                "/usr/share/kibana/plugins", str(ki_p), type=mount_type
            )
        ]
    else:
        el_mnts, ki_mnts = [], []
    if error_if_exists or not len(client.containers.list(filters={"name": el_name})):
        client.containers.run(
            el_im,
            name=el_name,
            detach=True,
            remove=rm,
            network=network,
            ports={"9200": elastic_port},
            environment=el_env,
            mounts=el_mnts,
            ulimits=el_ulimits,
        )
    elastic_port = client.api.inspect_container(el_name)["NetworkSettings"]["Ports"][
        "9200/tcp"
    ][0]["HostPort"]

    ki_name = prefix + "_kibana"
    ki_env = [
        f"ELASTIC_PASSWORD={elastic_password}",
        "SERVER_NAME=kibana",
        f"ELASTICSEARCH_URL=http://{el_name}:9200",
        f"ELASTICSEARCH_HOSTS=http://{el_name}:9200",
    ]
    if error_if_exists or not len(client.containers.list(filters={"name": ki_name})):
        client.containers.run(
            ki_im,
            name=ki_name,
            detach=True,
            remove=rm,
            network=network,
            ports={"5601": kibana_port},
            environment=ki_env,
            mounts=ki_mnts,
        )
    kibana_port = client.api.inspect_container(ki_name)["NetworkSettings"]["Ports"][
        "5601/tcp"
    ][0]["HostPort"]

    elk = None
    # TODO find docker containers IP
    elk = elastic.ElasticStack(elastic_port=elastic_port, kibana_port=kibana_port)
    if set_as_default_elk:
        elastic.set_default_elk(elk)

    return elk


def get_network(network, client=dockerpy.from_env(), create=True):
    nets = [n for n in client.networks.list(names=[network]) if n.name == network]
    if len(nets) == 1:
        return nets[0]
    if create:
        return client.networks.create(network)
    else:
        return None


def get_container(name, client=dockerpy.from_env(), raise_error=None):
    c = [_ for _ in client.containers.list(filters={"name": name}) if _.name == name]
    return c[0] if len(c) == 1 else None


def container_running(name, client=dockerpy.from_env(), raise_error=None):
    c = get_container(name, client=client)
    if c is not None and c.status == "running":
        return True
    if raise_error:
        msg = (
            raise_error
            if isinstance(raise_error, str)
            else f"container {name} not running"
        )
        raise RuntimeError(msg)


def elastic_stack_from_docker(
    container_prefix, set_as_default_elk=True, raise_error=False
):
    el_name, ki_name = container_prefix + "_elastic", container_prefix + "_kibana"
    client = dockerpy.from_env()
    if not container_running(el_name, client=client, raise_error=raise_error):
        return None
    elastic_port = client.api.inspect_container(el_name)["NetworkSettings"]["Ports"][
        "9200/tcp"
    ][0]["HostPort"]
    kibana_port = client.api.inspect_container(ki_name)["NetworkSettings"]["Ports"][
        "5601/tcp"
    ][0]["HostPort"]
    from . import elastic

    es = elastic.ElasticStack(elastic_port=elastic_port, kibana_port=kibana_port)
    if set_as_default_elk:
        elastic.set_default_elk(es)
    return es


def stop_elastic_on_docker(container_prefix):
    client = dockerpy.from_env()
    for c in client.containers.list(filters={"name": container_prefix + "_"}):
        c.stop()
    n = get_network(f"{container_prefix}_network", create=False)
    if n:
        n.reload()
        for c in n.containers:
            n.disconnect(c, force=True)
            print(f"remove {c.name} from {n.name}")
        n.remove()
