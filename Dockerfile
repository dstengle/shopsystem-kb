# kb's image: `kb serve` over a store at /data, at port 50051. Published: the store directory (/data), the port
# (50051), the entry point (kb) and the default command; what is below them is not. KB_ACTOR has no default: whoever
# starts a store names the role.

# The first stage builds kb's wheel and installs it, with its runtime dependencies alone, into a virtualenv that holds
# no pip; the second takes only that virtualenv, onto the base image with its own pip taken out.
FROM python:3.12.15-slim AS build
WORKDIR /src
COPY pyproject.toml ./
COPY src ./src
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /wheels . \
 && python -m venv --without-pip /opt/kb \
 && python -m pip --python /opt/kb/bin/python install --no-cache-dir /wheels/*.whl

FROM python:3.12.15-slim
RUN groupadd --gid 1000 kb \
 && useradd --uid 1000 --gid kb --no-create-home --shell /usr/sbin/nologin kb \
 && mkdir /data && chown kb:kb /data \
 && python -m pip uninstall --yes --quiet pip
COPY --from=build /opt/kb /opt/kb
ENV PATH="/opt/kb/bin:$PATH"
USER kb
WORKDIR /data
VOLUME /data
EXPOSE 50051
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 \
  CMD ["/opt/kb/bin/python", "-c", "import socket; socket.create_connection(('127.0.0.1', 50051), 2).close()"]
ENTRYPOINT ["kb"]
CMD ["serve", "/data", "--listen", "0.0.0.0:50051", "--start"]
