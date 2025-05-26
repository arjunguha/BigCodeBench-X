FROM docker.io/eclipse-temurin:24-jdk
MAINTAINER "Zixuan Wu <wu.zixua@northeastern.edu>"
RUN apt-get update -q
RUN apt-get install -yq python3-pip
RUN pip3 install --break-system-packages bounded_subprocess==1.3.0

# Install Maven for dependency management
RUN apt-get install -yq maven

ENV JAVA_DEPS_PATH=/java_deps
RUN mkdir -p $JAVA_DEPS_PATH

COPY TryInstallDependencies.java /TryInstallDependencies.java
COPY libs.txt /libs.txt

# Create minimal Maven project structure
RUN mkdir -p /maven_project/src/main/java
COPY pom_template.xml /maven_project/pom.xml

# Compile and run TryInstallDependencies to install dependencies listed in libs.txt
RUN javac -cp ".:$JAVA_DEPS_PATH/*" /TryInstallDependencies.java -d . && \
    java -cp ".:$JAVA_DEPS_PATH/*" TryInstallDependencies /libs.txt

# / (root directory)
# ├── TryInstallDependencies.java
# ├── TryInstallDependencies.class    #(compiled)
# ├── libs.txt
# ├── java_deps/                      # FILLED WITH JARS
# │   ├── jackson-core-2.15.2.jar...
# └── maven_project/
#     ├── pom.xml
#     └── src/main/java/

# Set CLASSPATH environment variable so that java runs can find the installed libraries
ENV CLASSPATH="$JAVA_DEPS_PATH/*:."

# It turns out that the Python test suites use pandas.
RUN apt-get install -yq python3-pandas python3-pytest python3-sklearn

COPY entrypoint.py /entrypoint.py
COPY driver.py /driver.py

ENTRYPOINT ["/usr/bin/python3", "/entrypoint.py"]