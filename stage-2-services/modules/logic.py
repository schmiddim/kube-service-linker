import logging
from .kube import create_or_update_configmap, load_config, mount_configmap_as_env_var
import inflection

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)

load_config()


def analyze_requirements(response_data):
    logger.info("=== Try to map Services===")
    if len(response_data.get('exposed_services')) == 0:
        logger.info("No exposed services")
        return
    if len(response_data.get("deployments_with_requirements")) == 0:
        logger.info("No deployments with requirements")
        return

    for deployment in response_data.get("deployments_with_requirements"):
        deployment_name = deployment.get('deployment').get('name')
        deployment_namespace = deployment.get('deployment').get('namespace')
        if deployment.get('event') not in ['ADDED', 'MODIFIED']:
            raise Exception("implement for method", deployment)
        for service in response_data.get('exposed_services'):

            if service.get('event') not in ['ADDED', 'MODIFIED']:
                raise Exception("implement for method", service)

            for label, value in service.get('service').get('labels').items():
                for requirement in deployment.get("requirements"):

                    if label == 'decMgmtProvides':
                        if requirement.get('name') == value:
                            logger.info("Depl {} in ns {} requirements {} fulfilled by {} ".format(
                                deployment_name,
                                deployment_namespace,
                                requirement,
                                label)

                            )
                            requirement_name = requirement.get('name')
                            config_map_name = "service-linker-{}-{}-endpoint".format(deployment_name,
                                                                                     requirement_name.lower())
                            service_namespace = service.get('service').get('namespace')
                            service_name = service.get('service').get('name')
                            service_port = service.get('service').get('ports')[0].get('port')
                            cm_data = {"url": "http://{}.{}:{}".format(service_name, service_namespace, service_port)}

                            create_or_update_configmap(namespace=deployment_namespace, name=config_map_name,
                                                       data=cm_data,labels= [{"created-by": "kube-service-linker"}])
                            mount_configmap_as_env_var(deployment_name, deployment_namespace, config_map_name,
                                                       "ENDPOINT_{}".format(
                                                           inflection.underscore(requirement_name)).upper())
