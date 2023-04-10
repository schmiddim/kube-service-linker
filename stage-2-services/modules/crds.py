from kubernetes import client
from kubernetes.client import V1CustomResourceDefinition, V1CustomResourceDefinitionNames, V1CustomResourceDefinitionSpec, V1CustomResourceValidation, V1JSONSchemaProps
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)


def create_service_requirement_crd():

    api_instance = client.ApiextensionsV1Api()

    crd_name = "servicerequirements.kubeservicelinker.com"

    try:
        api_instance.read_custom_resource_definition(crd_name)
        logger.info(f"CRD {crd_name} already exists.")
    except client.rest.ApiException as e:
        if e.status == 404:
            crd = V1CustomResourceDefinition(
                api_version="apiextensions.k8s.io/v1",
                kind="CustomResourceDefinition",
                metadata=client.V1ObjectMeta(name=crd_name),
                spec=V1CustomResourceDefinitionSpec(
                    group="kubeservicelinker.com",
                    versions=[
                        client.V1CustomResourceDefinitionVersion(
                            name="v1",
                            served=True,
                            storage=True,
                            schema=V1CustomResourceValidation(
                                open_apiv3_schema=V1JSONSchemaProps(
                                    type="object",
                                    properties={
                                        "spec": V1JSONSchemaProps(
                                            type="object",
                                            properties={
                                                "requiresService": V1JSONSchemaProps(type="string"),
                                                "versionRange": V1JSONSchemaProps(
                                                    type="string",
                                                    pattern="^((\\^|<|>|<=|>=)?\\d+(\\.\\d+)?(\\.\\d+)?([+-].*)?)(\\s*(\\|\\||\\s)\\s*(\\^|<|>|<=|>=)?\\d+(\\.\\d+)?(\\.\\d+)?([+-].*)?)*$"
                                                ),
                                                "namespace": V1JSONSchemaProps(type="string"),
                                                "deployment": V1JSONSchemaProps(type="string"),
                                            },
                                            required=["requiresService", "versionRange", "namespace", "deployment"]
                                        )
                                    }
                                )
                            )
                        )
                    ],
                    names=V1CustomResourceDefinitionNames(
                        kind="ServiceRequirement",
                        plural="servicerequirements",
                        singular="servicerequirement"
                    ),
                    scope="Namespaced"
                )
            )

            try:
                api_instance.create_custom_resource_definition(body=crd)
                logger.info(f"CRD {crd_name} created.")
            except client.rest.ApiException as e:
                logger.error(f"Error creating CRD {crd_name}: {e}")
        else:
            logger.error(f"Error checking for existing CRD {crd_name}: {e}")


