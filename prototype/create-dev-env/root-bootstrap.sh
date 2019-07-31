#!/bin/bash

# Print commands and exit on errors
set -xe

apt-get update

KERNEL=$(uname -r)
DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
apt-get install -y --no-install-recommends \
  autoconf \
  automake \
  bison \
  build-essential \
  ca-certificates \
  clang \
  cmake \
  cpp \
  curl \
  emacs24 \
  flex \
  git \
  iproute2 \
  libboost-dev \
  libboost-filesystem-dev \
  libboost-iostreams1.58-dev \
  libboost-program-options-dev \
  libboost-system-dev \
  libboost-test-dev \
  libboost-thread-dev \
  libc6-dev \
  libelf-dev \
  libevent-dev \
  libffi-dev \
  libfl-dev \
  libgc-dev \
  libgc1c2 \
  libgflags-dev \
  libgmp-dev \
  libgmp10 \
  libgmpxx4ldbl \
  libjudy-dev \
  libpcap-dev \
  libreadline6 \
  libreadline6-dev \
  libssl-dev \
  libtool \
  linux-headers-$KERNEL\
  llvm \
  make \
  mktemp \
  net-tools \
  pkg-config \
  python \
  python-dev \
  python-ipaddr \
  python-pip \
  python-scapy \
  python-setuptools \
  tcpdump \
  unzip \
  vim \
  wget \
  xcscope-el \
  xterm \
  software-properties-common \
  python-software-properties

sudo python -m pip install psutil pyroute2 ply scapy==2.4.0
#sudo python3 -m pip install sqlalchemy flask pandas configparser sklearn
