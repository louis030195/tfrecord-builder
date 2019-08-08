FROM gitpod/workspace-full

# Create a virtualenv for dependencies. This isolates these packages from
# system-level packages.
# Use -p python3 or -p python3.7 to select python version. Default is version 2.
#RUN python3 -m virtualenv /env

# Setting these environment variables are the same as running
# source /env/bin/activate.
#ENV VIRTUAL_ENV /env
#ENV PATH /env/bin:$PATH

# Copy the application's requirements.txt and run pip to install all
# dependencies into the virtualenv.
#ADD requirements.txt /workspace/requirements.txt
#RUN pip install -r /workspace/requirements.txt

# Add the application source code.
#ADD . /workspace
USER root

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
 && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
 && sudo apt-get update \
 && sudo apt-get install -y google-cloud-sdk \
 && sudo rm -rf /var/lib/apt/lists/* \
 && sudo pip install requests


USER gitpod

RUN pip install -r requirements.txt

# Give back control
USER root

