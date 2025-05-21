FROM docker.io/r-base:4.5.0
MAINTAINER "Carolyn Anderson <ca101@wellesley.edu>"
RUN apt-get update -q
RUN apt-get install -yq python3-pip
RUN pip3 install --break-system-packages bounded_subprocess==1.3.0

RUN apt-get install -y r-cran-rcpparmadillo r-cran-caret r-cran-rcurl r-cran-dplyr r-cran-jpeg r-cran-cluster r-cran-zoo r-cran-mgcv r-cran-writexl r-cran-digest r-cran-stringr r-cran-png r-cran-fs r-cran-wordcloud r-cran-combinat r-cran-tzdb r-cran-rsqlite r-cran-shiny r-cran-hexbin r-cran-readxl r-cran-ggplot2 r-cran-magick r-cran-htmltools r-cran-stringdist r-cran-rgl r-cran-lubridate r-cran-mime r-cran-openssl r-cran-data.table r-cran-cli r-cran-uuid r-cran-openxlsx r-cran-bindrcpp r-cran-tm r-cran-xml2 r-cran-mixtools r-cran-zip r-cran-irlba r-cran-jsonlite r-cran-tidyr r-cran-httr r-cran-magrittr r-cran-reshape2 r-cran-vroom r-cran-base64enc r-cran-tidytext r-cran-ggpubr r-cran-corrplot r-cran-readr r-cran-dbscan r-cran-tidyverse

COPY install_packages.R /install_packages.R
RUN Rscript /install_packages.R

# It turns out that the Python test suites use pandas.
RUN apt-get install -yq python3-pandas python3-pytest python3-sklearn

COPY entrypoint.py /entrypoint.py
COPY driver.py /driver.py


ENTRYPOINT ["/usr/bin/python3", "/entrypoint.py"]
