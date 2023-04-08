import logging as log
import os

import requests
from kubernetes import client, watch

from modules.kube import load_config

log.getLogger().setLevel(log.INFO)


def service_to_dict(service):
    return {
        'name': service.metadata.name,
        'namespace': service.metadata.namespace,
        'labels': service.metadata.labels
    }


def extract_requires_labels(labels):
    requires_labels = []

    groups = set()
    for key in labels.keys():
        if key.startswith("decMgmtRequires"):
            # Split the key by '-' and get the second part (group)
            group = key.split("-")[1]
            groups.add(group)

    for group in groups:
        group_dict = {}
        for key, value in labels.items():
            if key.startswith(f"decMgmtRequires-{group}"):
                # Split the key by '-' and get the third part (label_type)
                label_type = key.split("-")[2]
                group_dict[label_type] = value
        requires_labels.append(group_dict)

    return requires_labels


def watch_for_services():
    log.info("=== Looking for Services===")
    w = watch.Watch()
    return_objects = []
    for event in w.stream(client.CoreV1Api().list_service_for_all_namespaces, timeout_seconds=10):
        if event['object'].metadata.labels is None:
            continue

        for key, value in event['object'].metadata.labels.items():
            if key == 'decMgmtProvides':
                return_objects.append({
                    "event": event['type'],
                    "offers": value,
                    "service": event['object']
                })

    return return_objects


def watch_for_deployments():
    log.info("=== Looking for Deployments===")
    w = watch.Watch()
    return_objects = []
    v1 = client.AppsV1Api()

    for event in w.stream(v1.list_deployment_for_all_namespaces, timeout_seconds=10):
        requirements = []
        if event['object'].metadata.labels is None:
            continue
        requires_labels = extract_requires_labels(event['object'].metadata.labels)
        for key, value in event['object'].metadata.labels.items():
            print("Requires Labels:", requires_labels)
            if key.startswith("decMgmtRequires-name"):
                requirements.append(value)

        if len(requires_labels) > 0:
            return_objects.append({
                "event": event['type'],
                "requirements": requires_labels,
                "deployment": event['object']

            })
    return return_objects


def send_data_to_endpoint(exposed_services, deployments_with_requirements, url):
    for deployment in deployments_with_requirements:
        deployment['deployment'] = service_to_dict(deployment.get('deployment'))

    for service in exposed_services:
        service['service'] = service_to_dict(service.get('service'))

    data = {
        "deployments_with_requirements": deployments_with_requirements,
        "exposed_services": exposed_services
    }
    headers = {'Content-type': 'application/json'}
    try:

        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            log.error("unable to send data")
        else:
            log.info(response.status_code)
            log.info(response.json())
    except Exception as e:
        log.error("Error sending data to {}, {}".format(url, e))


def main():
    load_config()
    while True:
        exposed_services = watch_for_services()
        deployments_with_requirements = watch_for_deployments()
        endpoint = os.getenv("ENDPOINT_API", "http://localhost:9000")
        send_data_to_endpoint(exposed_services, deployments_with_requirements, endpoint)


if __name__ == '__main__':
    main()
    load_config()
