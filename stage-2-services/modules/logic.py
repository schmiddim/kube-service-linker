import logging
from .kube import create_or_update_configmap, load_config, mount_configmap_as_env_var, mount_configmaps_as_env_var

import inflection

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)

load_config()


def find_service_for_requirement(requirement, services):
    """
    @todo: version check from localcrdtest.py!!!!!!
    @todo: handle fuckling events!!!

      if semver.match(provided_version, version_range):
    :param requirement:
    :param services:
    :return:
    """
    for service in services:
        for label, value in service.get('service').get('labels').items():
            if label == 'decMgmtProvides':
                if requirement == value:
                    return service.get('service')
    return None


def make_configmap(service_name, service_namespace, service_port, deployment_name, deployment_namespace,
                   requirement_name):
    config_map_name = "service-linker-{}-{}-endpoint".format(deployment_name,
                                                             requirement_name.lower())

    cm_data = {"url": "http://{}.{}:{}".format(service_name, service_namespace, service_port)}
    create_or_update_configmap(namespace=deployment_namespace, name=config_map_name,
                               data=cm_data, labels=[{"created-by": "kube-service-linker"}])
    return config_map_name


def analyze_requirements(response_data):
    deployments_to_modify = {}
    logger.info("=== Try to map Services===")
    if len(response_data.get('exposed_services')) == 0:
        logger.info("No exposed services")
        return

    for service_requirement in response_data.get('service_requirements'):
        requires_service = service_requirement.get('service_requirement').get('requires_service')
        service_requirement_name = service_requirement.get('service_requirement').get('name')
        service_requirement_namespace = service_requirement.get('service_requirement').get('namespace')
        if service_requirement.get('event') not in ['ADDED', 'MODIFIED']:
            raise Exception("implement for method", service_requirement)

        service = find_service_for_requirement(requires_service, response_data.get('exposed_services'))
        if service is None:
            print("requirement {} could not be fulfilled".format(service_requirement))
            continue

        config_map_name = make_configmap(
            service.get('namespace'),
            service.get('name'),
            service.get('ports')[0].get('port'),
            service_requirement_name,
            service_requirement_namespace,
            requires_service
        )
        # @todo exits because of race conditions!

        key = "{}%{}".format(service_requirement_name, service_requirement_namespace)
        if deployments_to_modify.get(key) is None:
            deployments_to_modify[key] = []
            deployments_to_modify[key].append(
                {
                    'deployment_name': service_requirement_name,
                    'deployment_namespace': service_requirement_namespace,
                    'config_map_name': config_map_name,
                    'env_var_name': "ENDPOINT_{}".format(
                        inflection.underscore(requires_service)).upper()

                }
            )
        mount_configmap_as_env_var(service_requirement_name, service_requirement_namespace, config_map_name,
                                   "ENDPOINT_{}".format(
                                       inflection.underscore(requires_service)).upper())

    for deployment in response_data.get("deployments_with_requirements"):
        deployment_name = deployment.get('deployment').get('name')
        deployment_namespace = deployment.get('deployment').get('namespace')
        if deployment.get('event') not in ['ADDED', 'MODIFIED']:
            raise Exception("implement for method", deployment)

        for required_service in deployment.get("requirements"):
            requirement_name = required_service.get('name')
            service = find_service_for_requirement(requirement_name, response_data.get('exposed_services'))
            if service is None:
                print("requirement {} could not be fulfilled".format(required_service))
                continue

            config_map_name = make_configmap(
                service.get('namespace'),
                service.get('name'),
                service.get('ports')[0].get('port'),
                deployment_name,
                deployment_namespace,
                requirement_name
            )
            key = "{}%{}".format(deployment_name, deployment_namespace)

            if deployments_to_modify.get(key) is None:
                deployments_to_modify[key] = []
            deployments_to_modify[key].append(
                {
                    'deployment_name': deployment_name,
                    'deployment_namespace': deployment_namespace,
                    'config_map_name': config_map_name,
                    'env_var_name': "ENDPOINT_{}".format(
                        inflection.underscore(requirement_name)).upper()

                }
            )

            mount_configmap_as_env_var(deployment_name, deployment_namespace, config_map_name,
                                       "ENDPOINT_{}".format(
                                           inflection.underscore(requirement_name)).upper())

    for key, deployments in deployments_to_modify.items():
        config_maps = []
        env_var_names = []

        for deployment in deployments:
            config_maps.append(deployment.get('config_map_name'))
            env_var_names.append(deployment.get('env_var_name'))

        name, namespace = key.split("%")
        mount_configmaps_as_env_var(
            deployment_name=name,
            target_namespace=namespace,
            config_maps=config_maps,
            env_var_names=env_var_names

        )

