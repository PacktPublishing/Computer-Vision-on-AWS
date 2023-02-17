# Define function directory
ARG FUNCTION_DIR="/var/task"

FROM python:3.7.9 as build
RUN apt-get -y update && \
  apt-get -y install libgl1-mesa-dev python3-opencv && \  
  rm -rf /var/cache/apt/*

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

WORKDIR ${FUNCTION_DIR}

# Build the app...
COPY requirements.txt .
RUN pip install -r requirements.txt -t ${FUNCTION_DIR}
COPY . .

FROM amazonlinux:2 as target
ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}

WORKDIR ${FUNCTION_DIR}

# Install Dependencies...
RUN yum -y update && yum -y install \ 
  mesa-libGL.x86_64 \
  opencv-python.x86_64 \
  python3

# Setup application
COPY --from=build ${FUNCTION_DIR} ${FUNCTION_DIR}
RUN chmod a+x app.py

# CMD [ "app.handler" ]
ENTRYPOINT [ "/var/task/app.py" ]
