docker build --tag=collapsebob/sigma .
docker kill collapsebob
docker rm collapsebob
docker run -d --name collapsebob collapsebob/sigma