# Kube Service Linker

![progress-banner](https://i.imgur.com/y9Kdi8O.jpg)


Reads labels from Services and Deployments
## Informer 
just run informer.py

## Webhook
create ngrok, modifiy endpoint in webhook.yaml according to the output from 
```
ngrok http http://localhost:8085
```
Not implemented and not the best idea for this project


Further approaches would be 
- Events
- 
- Kubernetes Informers


## Todos
- Linkerd Support
- Istio Support

- was wenn label kaputt? wildcards?
- secret und kind verwursteln
