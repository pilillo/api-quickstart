docker run -it \
-p 5000:5000 \
-e FLASK_ENV="development" \
api-quickstart:0.1

#docker run -p 5000:5000 -it --entrypoint /bin/sh api-quickstart:0.1
