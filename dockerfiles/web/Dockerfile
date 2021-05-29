FROM python:3.9-buster

WORKDIR /usr/src/app

ENV DEBIAN-FRONTEND noninteractive
ENV DISPLAY=:1
ENV GECKODRIVER_VERSION="v0.26.0"
RUN echo "deb http://deb.debian.org/debian stretch-backports main" > /etc/apt/sources.list.d/backports.list && \
    wget -O - https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get update && \
    apt-get install -y xvfb firefox-esr libpq-dev python3-dev nodejs && \
    apt-get install -y -t stretch-backports libsqlite3-0 && \
    apt-get clean

RUN wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    mkdir geckodriver && \
    tar -xzf geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz -C geckodriver

RUN npm install -g yarn && \
    mkdir /var/www ./node_modules /.cache /.yarn /.mozilla && \
    touch /usr/src/app/yarn-error.log
COPY yarn.lock /usr/src/app/
RUN chmod -R 777 /usr/src/app/ /var/lib/xkb /.cache /.yarn /.mozilla

COPY requirements.txt dev-requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY package.json /usr/src/app/
RUN yarn

COPY create_db.py /usr/src/app/
EXPOSE 3000

ENV PATH="/usr/src/app/geckodriver:${PATH}"
ENV SECRET_KEY 4Q6ZaQQdiqtmvZaxP1If
ENV SQLALCHEMY_DATABASE_URI postgresql://openoversight:terriblepassword@postgres/openoversight-dev

WORKDIR /usr/src/app/OpenOversight

CMD ["scripts/entrypoint.sh"]
