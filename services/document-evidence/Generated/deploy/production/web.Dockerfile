ARG NODE_IMAGE=node:24-alpine
ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.27-alpine

FROM ${NODE_IMAGE} AS build
ARG APPFORGE_FRONTEND_ROOT=frontend-app
WORKDIR /src
COPY . .
WORKDIR /src/${APPFORGE_FRONTEND_ROOT}
RUN test -f package-lock.json || (echo "package-lock.json is required. Generate the production frontend bundle before docker build." >&2; exit 1)
RUN npm ci
RUN npm run build

FROM ${NGINX_IMAGE} AS runtime
USER root
RUN apk add --no-cache curl
USER 101
ARG APPFORGE_FRONTEND_ROOT=frontend-app
COPY deploy/production/web-nginx.txt /etc/nginx/conf.d/default.conf
COPY --from=build /src/${APPFORGE_FRONTEND_ROOT}/dist /usr/share/nginx/html
EXPOSE 8080
