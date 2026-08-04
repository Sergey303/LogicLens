ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.27-alpine

FROM ${NGINX_IMAGE} AS runtime
USER root
RUN apk add --no-cache curl
USER 101
COPY deploy/production/proxy-nginx.txt /etc/nginx/conf.d/default.conf
EXPOSE 8080
