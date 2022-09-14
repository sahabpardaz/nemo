FROM docker/compose:debian-1.28.2
RUN apt-get update && apt-get install -y curl
ADD https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 /usr/local/bin/yq
RUN chmod a+x /usr/local/bin/yq
