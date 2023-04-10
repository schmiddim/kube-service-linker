import semver
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from modules.crds import create_service_requirement_crd

config.load_kube_config()

custom_api_instance = client.CustomObjectsApi()
core_api_instance = client.CoreV1Api()

group = "kubeservicelinker.com"
version = "v1"
plural = "servicerequirements"

create_service_requirement_crd()
try:
    service_requirements = custom_api_instance.list_cluster_custom_object(group, version, plural)
    items = service_requirements.get("items", [])

    for item in items:
        namespace = item["metadata"]["namespace"]
        required_service = item["spec"]["requiresService"]
        version_range = item["spec"]["versionRange"]

        try:
            services = core_api_instance.list_service_for_all_namespaces()
            for service in services.items:
                foo = service.metadata.name
                labels = service.metadata.labels

                if labels:
                    provided_service = labels.get("decMgmtProvides")
                    provided_version = labels.get("decMgmtVersion")
                    if provided_service == required_service:
                        if provided_version is None:
                            print("Match found but no Version label set for service {} in namespace {}".format(service.metadata.name,
                                                                                                service.metadata.namespace))
                            continue
                        if semver.match(provided_version, version_range):
                            print(f"Service {provided_service} with version {provided_version} is compatible.")
                        else:
                            print(f"Service {provided_service} with version {provided_version} is NOT compatible.")
        except ApiException as e:
            print(f"Error listing services in namespace {namespace}: {e}")

except ApiException as e:
    print(f"Error listing ServiceRequirement objects: {e}")
