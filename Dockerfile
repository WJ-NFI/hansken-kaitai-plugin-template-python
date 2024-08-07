# Multi-stage Dockerfile, to build and package an extraction plugin
#  Recommended way to build the plugin is by calling tox:
#    tox -e package
#  if you need to pass a proxy:
#    tox -e package -- --build-arg https_proxy=https://your-proxy
#  if you want to pass a private Python package index:
#     tox -e package -- --build-arg PIP_INDEX_URL=https://your-pypi-mirror

###############################################################################
# Stage 1: build the plugin
# use a 'fat' image to setup the dependencies we'll need

FROM python:3.12 AS builder
ARG PIP_INDEX_URL=https://pypi.org/simple/
# build wheels for all dependencies in /app/dist (compiling binary distributions for sdists containing non-python code)
RUN mkdir --parents /app/dist
COPY requirements.txt /app/requirements.txt
RUN pip wheel --requirement /app/requirements.txt --wheel-dir /app/dist


###############################################################################
# Stage 2: create the distributable plugin image
# use a 'slim' image for running the actual plugin

FROM python:3.12-slim
# copy and install the dependencies in wheel form from the builder
RUN mkdir --parents /app/dist
COPY --from=builder /app/dist/*.whl /app/dist/
RUN pip install --no-index /app/dist/*.whl

# copy the actual plugin file, run that on port 8999
COPY *.py /app/
COPY structs/* /app/structs/
EXPOSE 8999
ENTRYPOINT ["/usr/local/bin/serve_plugin", "-vv"]
RUN apt-get -y update; apt-get -y install curl
RUN curl -LO https://github.com/kaitai-io/kaitai_struct_compiler/releases/download/0.10/kaitai-struct-compiler_0.10_all.deb
RUN yes | apt-get install ./kaitai-struct-compiler_0.10_all.deb
RUN cd app/structs
RUN kaitai-struct-compiler -t python /app/structs/*.ksy
CMD ["/app/plugin.py", "8999"]
