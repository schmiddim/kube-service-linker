import time
from kubernetes import client, config, watch
import logging as log
import inflection

log.getLogger().setLevel(log.INFO)
exposedServices = {}
servicesWithRequirements = {}


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


def load_config(context=None):
    try:
        config.load_kube_config(context=context)
    except config.config_exception.ConfigException as e:
        log.info("Kube Config not found - try in cluster")
        log.info(e)
        config.load_incluster_config()


def create_configmap(namespace, name, data):
    load_config()

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


def watch_for_services(v1):
    log.info("=== Looking for Services===")
    w = watch.Watch()
    for event in w.stream(v1.list_service_for_all_namespaces, timeout_seconds=10):
        if event['object'].metadata.labels is None:
            continue

        global exposedServices
        for key, value in event['object'].metadata.labels.items():
            if key == 'decMgmtProvides':
                log.info("Seems to be managed {} {}".format(key, value))
                if exposedServices.get(value) is None:
                    log.info("{} is not registered yet - append".format(value))
                    exposedServices[value] = event['object']
                else:
                    if exposedServices.get(value) == event['object']:
                        log.info("{} is  already registered and not modified".format(value))
                    else:
                        log.info("{} is  already registered and modified - update".format(value))
                        exposedServices[value] = event['object']


def watch_for_deployments():
    log.info("=== Looking for Deployments===")
    w = watch.Watch()
    global servicesWithRequirements
    v1 = client.AppsV1Api()

    for event in w.stream(v1.list_deployment_for_all_namespaces, timeout_seconds=10):
        if event['object'].metadata.labels is None:
            continue
        for key, value in event['object'].metadata.labels.items():
            if key.startswith("decMgmtRequires"):
                log.info("Seems to be managed {} {}".format(key, value))
                deployment_name = event['object'].metadata.name + '===' + event['object'].metadata.namespace
                if servicesWithRequirements.get(deployment_name) is None:
                    servicesWithRequirements[deployment_name] = []

                if value not in servicesWithRequirements.get(deployment_name):
                    log.info("Requirement {} for deployment {} is not registered yet - append".format(value,
                                                                                                      deployment_name))
                    servicesWithRequirements[deployment_name].append(value)
                else:
                    log.info("Requirement {} for deployment {} is already registered".format(value, deployment_name))


def analyze_requirements(exposed_services, services_with_requirements):
    log.info("=== Try to map Serices===")
    if len(exposed_services.keys()) == 0:
        log.info("No exposed services")
        return
    if len(services_with_requirements.keys()) == 0:
        log.info("No deployments with requirements")
        return

    for deployment, requirements in services_with_requirements.items():
        log.info("{} requires {}".format(deployment, requirements))
        for item in requirements:
            if item in exposed_services.keys():
                service = exposed_services.get(item)
                deployment_name, target_namespace = deployment.split("===")
                service_namespace = service.metadata.namespace
                service_name = service.metadata.name
                service_port = service.spec.ports[0].port
                config_map_name = "{}-{}-endpoint".format(service_name, service_namespace)

                data = {"url": "http://{}.{}:{}".format(service_name, service_namespace, service_port)}
                log.info("service {} provides the Requirement".format(item))
                create_configmap(target_namespace, config_map_name, data)

                """
                todo  mount a configmap with the service endpoint in format 
                
                servicename.namespace
                """
                log.info(
                    "mount configmap {} into deployment {} in namespace {}".format(config_map_name, deployment_name,
                                                                                   target_namespace))

                mount_configmap_as_env_var(deployment_name, target_namespace, config_map_name,
                                           "ENDPOINT_{}".format(inflection.underscore(item)).upper())

            else:
                log.info("unable to resolve dependency {}".format(item))

    pass


def main():
    load_config()

    v1 = client.CoreV1Api()
    while True:
        watch_for_services(v1)
        watch_for_deployments()
        analyze_requirements(exposed_services=exposedServices, services_with_requirements=servicesWithRequirements)
        log.info("Finished namespace stream. Sleep")


if __name__ == '__main__':
    main()
    load_config()
    v1 = client.CoreV1Api()
