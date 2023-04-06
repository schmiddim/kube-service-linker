import logging as log

from kubernetes import client, config


def load_config(context=None):
    try:
        config.load_kube_config(context=context)
    except config.config_exception.ConfigException as e:
        log.info("Kube Config not found - try in cluster")
        log.info(e)
        config.load_incluster_config()


def create_or_update_configmap(namespace, name, data):
    cm = client.V1ConfigMap()
    cm.metadata = client.V1ObjectMeta(name=name)
    cm.data = data
    api = client.CoreV1Api()

    try:

        api.create_namespaced_config_map(namespace=namespace, body=cm)
        log.info(f"ConfigMap {name} in ns {namespace} was created")
    except client.rest.ApiException as e:

        if e.status == 409:
            try:
                api.patch_namespaced_config_map(namespace=namespace, name=name, body=cm)
                log.info("ConfigMap {}  in namespace {} updated".format(name, namespace))

            except client.rest.ApiException as e:
                log.info(f"Error updating ConfigMap {name}: {e}")
        else:
            log.error("Error creating configmap {} {}".format(name, e))


def mount_configmap_as_env_var(deployment_name, target_namespace, config_map_name, env_var_name):
    config.load_kube_config()

    apps_v1 = client.AppsV1Api()

    deployment = apps_v1.read_namespaced_deployment(deployment_name, target_namespace)

    if not deployment.spec.template.spec.volumes:
        deployment.spec.template.spec.volumes = []

    if not deployment.spec.template.spec.containers[0].volume_mounts:
        deployment.spec.template.spec.containers[0].volume_mounts = []

    if not deployment.spec.template.spec.containers[0].env:
        deployment.spec.template.spec.containers[0].env = []

    volume_name = config_map_name
    volume_mount_path = "/path/to/mount"
    if volume_name not in [v.name for v in deployment.spec.template.spec.volumes]:
        volume = client.V1Volume(
            name=volume_name,
            config_map=client.V1ConfigMapVolumeSource(
                name=config_map_name
            )
        )

        deployment.spec.template.spec.volumes.append(volume)

    if volume_mount_path not in [vm.mount_path for vm in deployment.spec.template.spec.containers[0].volume_mounts]:
        volume_mount = client.V1VolumeMount(
            name=volume_name,
            mount_path=volume_mount_path,
            read_only=True
        )
        deployment.spec.template.spec.containers[0].volume_mounts.append(volume_mount)

    env_var = client.V1EnvVar(
        name=env_var_name,
        value_from=client.V1EnvVarSource(
            config_map_key_ref=client.V1ConfigMapKeySelector(
                name=config_map_name,
                key="url"
            )
        )
    )
    deployment.spec.template.spec.containers[0].env.append(env_var)
    apps_v1.patch_namespaced_deployment(
        deployment_name, target_namespace, deployment)
