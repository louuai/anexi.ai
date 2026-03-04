FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend-react/package.json ./
RUN npm install

COPY frontend-react/ ./
RUN npm run build

FROM nginx:alpine

RUN apk add --no-cache gettext

COPY frontend-react/nginx.default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
