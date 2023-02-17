FROM node:16

RUN apt-get -y update && apt-get -y install --no-install-recommends python3-pip npm curl zip groff \
  && npm install -g aws-cdk@2.1.0

# Uncomment for docker in docker support.
#RUN /usr/bin/python3 -m pip install --upgrade pip
#RUN curl -sSL https://get.docker.com/ | sh

WORKDIR /src

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY app.py .
RUN cdk synth -a ./app.py