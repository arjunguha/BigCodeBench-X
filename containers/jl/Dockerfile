FROM docker.io/julia:1.11.4-bookworm
MAINTAINER "Arjun Guha <a.guha@northeastern.edu>"
RUN apt-get update -q
RUN apt-get install -yq python3-pip
RUN pip3 install --break-system-packages bounded_subprocess==1.3.0

COPY try_install_packages.jl /try_install_packages.jl
COPY libs.txt /libs.txt

# Julia is one of those languages that likes to install packages to the
# home directory. With Docker/Podman, the default user is root and the home
# directory is /root within the container. The Apptainer story is a more
# complicated. You can read this if you like:
#
#     https://apptainer.org/docs/user/main/fakeroot.html
#
# Keep in mind that Northeastern Discovery uses an ancient Linux kernel that
# we probably want to support, and it uses Singularity, not Apptainer.
#
# Anyway, we set the JULIA_DEPOT_PATH so that packages are *not* installed
# to the home directory, which is the simplest way to avoid problems with
# Apptainer/Singularity.
ENV JULIA_DEPOT_PATH=/julia_depot
RUN JULIA_DEPOT_PATH=/julia_depot julia /try_install_packages.jl /libs.txt

# It turns out that the Python test suites use these libraries.
RUN apt-get install -yq python3-pandas python3-sklearn python3-pytest

COPY entrypoint.py /entrypoint.py
COPY driver.py /driver.py


ENTRYPOINT ["/usr/bin/python3", "/entrypoint.py"]
