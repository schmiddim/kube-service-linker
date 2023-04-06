
TAG=$(date +%s)
sed -i '/mysql/! s/\(image:.*:\).*$/\1'"$TAG"'/' deployment.yaml

nerdctl --namespace k8s.io build  -t my-python-app -f DockerfileInformer . -tinformer:$TAG
nerdctl --namespace k8s.io build  -t my-python-app -f DockerfileProcessing . -tprocessing:$TAG
kubectl apply -f deployment.yaml
