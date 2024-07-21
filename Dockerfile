FROM python:3.10.10-buster

ARG USERNAME="pcleaner"
ARG USER_ID="1000"
ARG LOGIN_SHELL="/bin/bash"

RUN useradd -m -s "${LOGIN_SHELL}" -N -u "${USER_ID}" "${USERNAME}"

ENV USER ${USERNAME}
ENV UID ${USER_ID}
ENV HOME /home/${USERNAME}
ENV PATH "${HOME}/.local/bin/:${PATH}"

# We need to install libgl1 dependencies to use opencv.
# Also, include vim and nano to be able to edit profiles.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libdbus-1-dev \
        dbus \
        vim \
        nano

# Install pcleaner
RUN pip install pcleaner

RUN mkdir /app && chown ${UID} /app

USER ${USERNAME}

WORKDIR /app

CMD bash

