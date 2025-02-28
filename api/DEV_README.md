# /etc/hosts
```
# starry
192.168.1.152 redis
192.168.1.152 sandbox
```

# [docker-compose-dev.yaml](..%2Fdocker-hz%2Fx86%2Fconf%2Fdocker-compose-dev.yaml)

# dev
> 192.168.1.151:5002

# test
> 192.168.1.152:5002

# prod
> 172.16.34.160

> conda activate py310
> nohup poetry run python -m flask run --host 0.0.0.0 --port=5002 --debug &


# docker
> sh build.sh

or

> git log -1 > commit_info.txt
> docker build -t docker.art.haizhi.com/starry-api-amd64:0.11.1 .