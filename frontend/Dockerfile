FROM node:16.14.0 AS build-env

WORKDIR /app/
COPY package.json .
COPY package-lock.json .
RUN npm install
COPY . .
RUN npm run build --only=production

FROM bash:5.1.4
RUN apk update && apk add rsync
COPY update-files-to-serve.sh .
RUN chmod +x update-files-to-serve.sh
COPY --from=build-env /app/build/ /local/frontend/
CMD ./update-files-to-serve.sh
