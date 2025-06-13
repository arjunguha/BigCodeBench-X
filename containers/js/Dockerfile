FROM docker.io/node:24
MAINTAINER "Arjun Guha <a.guha@northeastern.edu>"
RUN apt-get update -q
# Some of the Python test suites require these packages.
RUN apt-get install -yq python3-pip python3-pandas python3-sklearn
RUN pip3 install --break-system-packages bounded_subprocess==1.3.0

WORKDIR /root

COPY try_npm_install.sh /try_npm_install.sh

COPY libs.txt /libs.txt
RUN /try_npm_install.sh $(cat /libs.txt)
RUN /try_npm_install.sh pca pca-js @stdlib/stdlib pandas-js plotter ml5
RUN /try_npm_install.sh jimp plotly geolib fft-js plotly.js-dist \
    combinatorial-generators ml-gaussian-mixture z-score babel-runtime \
     random-forest-js chi-square-test simple-statistics sklearn.datasets k-means \
     fast-csv array fast-levenshtein collections curve-fit readdirp \
     math-random-seed ml-dbscan shapiro-wilk normality ml-standardize jszip \
     bcrypt simple-linear-regression stem-words chi-square seasonal-decompose \
      prophet danfojs-node yargs ml-logistic-regression randomforest \
      plotly.js-dist-min compute-correlation cheerio histogram ml-evaluation 

COPY entrypoint.py /entrypoint.py
COPY driver.py /driver.py

WORKDIR /root

ENTRYPOINT ["/usr/bin/python3", "/entrypoint.py"]
