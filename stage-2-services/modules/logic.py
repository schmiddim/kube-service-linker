import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)


def analyze_requirements(data):
    logger.info("=== Try to map Services===")
    if len(data.get('exposed_services')) == 0:
        logger.info("No exposed services")
        return
    if len(data.get("deployments_with_requirements")) == 0:
        logger.info("No deployments with requirements")
        return

    for deployment in data.get("deployments_with_requirements"):

        if deployment.get('event') not in ['ADDED', 'MODIFIED']:
            raise Exception("implement for method", deployment)
        for service in data.get('exposed_services'):

            if service.get('event') not in ['ADDED', 'MODIFIED']:
                raise Exception("implement for method", service)

            for label, value in service.get('service').get('labels').items():
                for requirement in deployment.get("requirements"):
                    if label == 'decMgmtProvides':
                        if requirement.get('name') == value:
                            logger.info("Depl {} in ns {} requirements {} fulfilled by {} ".format(
                                deployment.get('deployment').get('name'),
                                deployment.get('deployment').get('namespace'),
                                requirement,
                                label)
                            )
