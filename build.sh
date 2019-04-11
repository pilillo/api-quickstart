docker build \
--build-arg app_name="api-quickstart" \
--build-arg env_name="development" \
-t api-quickstart:0.1 -f Dockerfile .
