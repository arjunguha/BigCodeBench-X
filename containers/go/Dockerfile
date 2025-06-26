FROM golang:1.23-bullseye

# Update package list and install Python dependencies
RUN apt-get update -q
RUN apt-get install -yq python3-pip python3-pandas python3-pytest python3-sklearn

# Install bounded_subprocess for Python
RUN pip3 install bounded_subprocess==1.3.0

# Set up Go environment
ENV GO111MODULE=on
ENV GOPROXY=https://proxy.golang.org,direct
ENV GOSUMDB=sum.golang.org

# Create a global module for pre-installing packages
ENV GLOBAL_GO_PATH=/go_global
RUN mkdir -p $GLOBAL_GO_PATH
WORKDIR $GLOBAL_GO_PATH

# Copy dependencies list
COPY libs.txt /libs.txt

# Initialize global module and install packages with error handling
RUN go mod init global_packages && \
    while IFS= read -r package; do \
        if [ ! -z "$package" ] && [ "${package#\#}" = "$package" ]; then \
            echo "Installing $package..."; \
            go get "$package@latest" || echo "Failed to install $package"; \
        fi; \
    done < /libs.txt && \
    go mod tidy || true

# Copy Python execution scripts
COPY entrypoint.py /entrypoint.py
COPY driver.py /driver.py

# Set working directory back to root
WORKDIR /

ENTRYPOINT ["/usr/bin/python3", "/entrypoint.py"]
