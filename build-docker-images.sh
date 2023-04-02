cd services
for folder in *service
do

    cd $folder
    echo $folder
#    docker build  -t$folder:2.0 .
     nerdctl --namespace k8s.io build -t$folder:2.2 .

#    ~/.rd/bin/docker push $folder:2.0
    ls
    cd -

done
