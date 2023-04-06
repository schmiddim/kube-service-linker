import logging as log

import inflection
from kubernetes import client, watch

from modules.kube import load_config, create_or_update_configmap, mount_configmap_as_env_var

log.getLogger().setLevel(log.INFO)


def watch_for_services():
    log.info("=== Looking for Services===")
    w = watch.Watch()
    exposed_services = {}
    for event in w.stream(client.CoreV1Api().list_service_for_all_namespaces, timeout_seconds=10):
        if event['object'].metadata.labels is None:
            continue

        for key, value in event['object'].metadata.labels.items():
            if key == 'decMgmtProvides':
                log.info("Seems to be managed {} {}".format(key, value))
                if exposed_services.get(value) is None:
                    log.info("{} is not registered yet - append".format(value))
                    exposed_services[value] = event['object']
                else:
                    if exposed_services.get(value) == event['object']:
                        log.info("{} is  already registered and not modified".format(value))
                    else:
                        log.info("{} is  already registered and modified - update".format(value))
                        exposed_services[value] = event['object']
    return exposed_services


def watch_for_deployments():
    log.info("=== Looking for Deployments===")
    w = watch.Watch()
    deployments_with_requirements = {}
    v1 = client.AppsV1Api()

    for event in w.stream(v1.list_deployment_for_all_namespaces, timeout_seconds=10):
        if event['object'].metadata.labels is None:
            continue
        for key, value in event['object'].metadata.labels.items():
            if key.startswith("decMgmtRequires"):
                log.info("Seems to be managed {} {}".format(key, value))
                deployment_name = event['object'].metadata.name + '===' + event['object'].metadata.namespace
                if deployments_with_requirements.get(deployment_name) is None:
                    deployments_with_requirements[deployment_name] = []

                if value not in deployments_with_requirements.get(deployment_name):
                    log.info("Requirement {} for deployment {} is not registered yet - append".format(value,
                                                                                                      deployment_name))
                    deployments_with_requirements[deployment_name].append(value)
                else:
                    log.info("Requirement {} for deployment {} is already registered".format(value, deployment_name))
    return deployments_with_requirements


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
                create_or_update_configmap(target_namespace, config_map_name, data)

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

    while True:
        exposed_services = watch_for_services()
        deployments_with_requirements = watch_for_deployments()
        analyze_requirements(exposed_services=exposed_services,
                             services_with_requirements=deployments_with_requirements)
        log.info("Finished namespace stream. Sleep")


if __name__ == '__main__':
    main()
    load_config()
