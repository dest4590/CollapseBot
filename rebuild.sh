docker build --tag=collapsebob/sigma .
docker kill collapsebob
docker rm collapsebob
docker run collapsebob/sigma --name collapsebob