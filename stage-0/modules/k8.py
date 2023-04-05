import logging as log

import kubernetes.client
from kubernetes import config, client


def load_config(context=None):
    try:
        config.load_kube_config(context=context)
    except config.config_exception.ConfigException as e:
        log.info("Kube Config not found - try in cluster")
        log.info(e)
        config.load_incluster_config()



def create_configmap(namespace, name, data):
    # Laden der Kubernetes-Konfiguration
    load_config()

    # Erstellen des V1ConfigMap-Objekts
    cm = client.V1ConfigMap()
    cm.metadata = client.V1ObjectMeta(name=name)
    cm.data = data

    # Initialisieren des Kubernetes API-Clients
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
            log.error("Error creating configmap {} {}".format(name, e ))

