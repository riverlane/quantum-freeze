# 1  python
# 2  python3
# 3  yum search python
# 4  yum install gcc openssl-devel bzip2-devel
# 5  wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
# 6  yum install wget
# 7  wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz
# 8  tar xzf Python-3.7.0.tgz
# 9  cd Python-3.7.0
# 10  ./configure --enable-optimizations
# 11  make altinstall
# 12  yum groupinstall "Development Tools"
# 13  make altinstall
# 14  ./configure --enable-optimizations
# 15  gcc
# 16  g++
# 17  make altinstall -j
# 18  sudo yum install libffi-devl
# 19  yum install libffi-devel
# 20  sudo yum install libffi-devl
# 21  make altinstall -j
# 22  history

FROM centos:7.6.1810

RUN yum install gcc openssl-devel bzip2-devel wget libffi-devel -y &&\
  yum groupinstall "Development Tools" -y &&\
  wget https://www.python.org/ftp/python/3.7.0/Python-3.7.0.tgz &&\
  tar xzf Python-3.7.0.tgz &&\
  cd Python-3.7.0 &&\
  ./configure --enable-optimizations --enable-shared &&\
  make altinstall -j

ENV LD_LIBRARY_PATH=/usr/local/lib
RUN ldconfig

COPY requirements.txt /game/
RUN cd /game && python3.7 -m venv venv && source venv/bin/activate &&\
  pip install -r requirements.txt pyinstaller

COPY pyquil_requests.py quantum-freeze.py README.md  requirements.txt  sprites.py /game/
COPY resources /game/resources
COPY qf-docker.spec /game/quantum-freeze.spec

RUN cd /game && source venv/bin/activate &&\
  pyinstaller quantum-freeze.spec
# fnamCOPYes =
# for fname in pyquil_requests.py quantum-freeze.py  quantum-freeze.spec  README.md  requirements.txt  resources  sprites.py
# do
# docker cp $fname distracted_blackwell:game/
# done
