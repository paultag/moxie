# VERSION   0.1
FROM        debian:unstable
MAINTAINER  Paul R. Tagliamonte <paultag@debian.org>

RUN echo "deb-src http://http.debian.net/debian/ unstable main" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y python3.4 python3-pip git
RUN apt-get update && apt-get build-dep -y python3-psycopg2
RUN mkdir -p /opt/pault.ag/
ADD . /opt/pault.ag/moxie/
RUN cd /opt/pault.ag/moxie; python3.4 /usr/bin/pip3 install -r requirements.txt
RUN adduser \
    --system \
    --home=/moxie \
    --shell=/bin/bash \
    --no-create-home \
    --group \
    moxie

USER moxie
CMD ["moxie-serve"]
