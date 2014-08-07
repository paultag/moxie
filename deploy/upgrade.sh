#!/bin/bash

source /etc/docker/moxie.sh

function moxierun {
    docker run --rm -it \
        -v /srv/lucifer.pault.ag/prod/moxie:/moxie \
        -e DATABASE_URL=${DATABASE_URL} \
        paultag/moxie \
        $@
}

cd ~tag/projects/moxie
git pull
docker build --rm -t paultag/moxie .

sudo service moxie stop
sudo service moxied stop

moxierun alembic -x sqlalchemy.url=${DATABASE_URL} upgrade head
docker rm moxie
docker rm moxied

sudo service moxie start
sudo service moxied start
sudo service nginx restart
