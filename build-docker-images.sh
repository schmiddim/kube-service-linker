cd services
for folder in *service
do

    cd $folder
    docker build  -t$folder:2.0 .
#    ~/.rd/bin/docker push $folder:2.0
    ls
    cd -

done