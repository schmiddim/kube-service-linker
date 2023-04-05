import time
from kubernetes import client, config, watch
import logging as log

from modules import k8

log.getLogger().setLevel(log.INFO)
exposedServices = {}
servicesWithRequirements = {}


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
                    log.info("Requirement {} for deployment {} is not registered yet - append".format(value, deployment_name))
                    servicesWithRequirements[deployment_name].append(value)
                else:
                    log.info("Requirement {} for deployment {} is already registered".format(value, deployment_name))


def analyze_requirements(exposed_services, services_with_requirements):
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
                config_map_name = "{}-{}-endpoint".format(service_name, service_namespace)
                data = {"url": "{}.{}".format(service_name, service_namespace)}
                k8.create_configmap(target_namespace, config_map_name, data)
                log.info("service {} provides the Requirement".format(item))

                """
                todo  mount a configmap with the service endpoint in format 
                
                servicename.namespace
                """

            else:
                log.info("unable to resolve dependency {}".format(item))

    pass


def main():
    k8.load_config()

    v1 = client.CoreV1Api()
    while True:
        watch_for_services(v1)
        watch_for_deployments()
        analyze_requirements(exposed_services=exposedServices, services_with_requirements=servicesWithRequirements)
        log.info("Finished namespace stream. Sleep")
        time.sleep(5)


if __name__ == '__main__':
    main()
    k8.load_config()
    v1 = client.CoreV1Api()
