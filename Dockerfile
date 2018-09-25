FROM python:3.6

WORKDIR /code

# Install tcp-port-wait.sh requirements
RUN apt-get update && apt-get install -y netcat

COPY ./requirements/base.txt requirements/base.txt
COPY ./requirements/production.txt requirements/production.txt
RUN pip install -r requirements/production.txt

ADD . /code

ARG environment=production
ENV environment=${environment}
RUN echo "Environment: $environment"

EXPOSE 8080
ENTRYPOINT ["bash", "/code/docker-entrypoint.sh"]
