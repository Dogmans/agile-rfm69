ARG IMAGE_VERSION=resin/armv7hf-debian:stretch
FROM ${IMAGE_VERSION} 

# Install dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
	python-dev \
	python-setuptools \
	python-pip \
	curl \
	libglib2.0-dev \
	libgirepository1.0-dev \
	python-gi \
	python-gi-cairo \
	python3-gi \
	python3-gi-cairo \
	gir1.2-gtk-3.0 \
	&& apt-get clean && rm -rf /var/lib/apt/lists/*
	
RUN	curl -O -J https://download.gnome.org/sources/glib/2.57/glib-2.57.1.tar.xz

# resin-sync will always sync to /usr/src/app, so code needs to be here.
WORKDIR /usr/src/app

COPY requirements.txt requirements.txt
RUN pip install wheel
RUN python -m pip install -r requirements.txt

COPY *.py ./

CMD ["python", "./run_server.py"]
