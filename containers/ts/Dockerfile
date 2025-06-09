FROM docker.io/node:24
RUN apt-get update -q
# Some of the Python test suites require these packages.
RUN apt-get install -yq python3-pip python3-pandas python3-sklearn
RUN pip3 install --break-system-packages bounded_subprocess==1.3.0

WORKDIR /root

COPY try_npm_install.sh /try_npm_install.sh

COPY libs.txt /libs.txt
RUN /try_npm_install.sh $(cat /libs.txt)
RUN /try_npm_install.sh typescript tsx canvas csv-parse plotly.js-dist csv-stringify \
    chartjs-node-canvas seedrandom plotly.js-dist-min @types/node mathjs \
    nodeplotlib luxon ml-pca papaparse ml-kmeans ts-node better-sqlite3 \
    date-fns ml-matrix simple-statistics danfojs-node node-canvas xlsx \
    chart.js open node-html-to-image node-fetch plotly.js sqlite3 \
    ml-levenberg-marquardt ml-regression-multivariate-linear dayjs \
    python-shell @tensorflow/tfjs-node jimp fft-js \
    node-forge ml-random-forest

COPY entrypoint.py /entrypoint.py
COPY driver.py /driver.py

RUN cat /install_log.txt

WORKDIR /root

ENTRYPOINT ["/usr/bin/python3", "/entrypoint.py"]
