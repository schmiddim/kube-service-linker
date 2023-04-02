TAG=$(date +%s)

#sed -i "s/\(image:.*:\).*$/\1$TAG/" k8/resources/*yaml
sed -i '/mysql/! s/\(image:.*:\).*$/\1'"$TAG"'/' k8/resources/*yaml
kubectl apply -k  k8


cd services
for folder in *service
do

    cd $folder
    echo $folder
#    docker build  -t$folder:2.0 .
     nerdctl --namespace k8s.io build -t$folder:$TAG .

#    ~/.rd/bin/docker push $folder:2.0
    ls
    cd -

done

