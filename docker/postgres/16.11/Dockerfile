## Postgres 18.1 on Debian Bookworm
## - Debian Bookworm refers to Debian 12
## - 18.1 is the latest stable Postgres as of 2026-01-06
## - However, FEHD needs older 16.X for compatibility with some extensions
##   So, it will use 16.11-bookworm instead
##FROM postgres:18.1-bookworm
FROM postgres:16.11-bookworm

## install frequently used utilities
## - '-ex' where '-e' exit on error, '-x' print commands as they are executed
RUN set -ex; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  acl \
  tmux \
  tree \
  vim \
  pv \
  jq \
  # Optional: Additional useful tools
  htop \
  nano \
  wget \
  curl \
  openssl \
  procps \
  net-tools \
  iputils-ping \
  ##  Important: pgvector extension for vector embeddings for postgres 18.x
  postgresql-18-pgvector \
  ; \
  rm -rf /var/lib/apt/lists/*

## copy common linux configs
COPY ./config/.inputrc /root/.inputrc
COPY ./config/.vimrc /root/.vimrc
COPY ./config/.tmux.conf /root/.tmux.conf
COPY ./config/.bashcfg.sh /root/.bashcfg.sh
w
COPY ./config/.inputrc /var/lib/postgresql/.inputrc
COPY ./config/.vimrc /var/lib/postgresql/.vimrc
COPY ./config/.tmux.conf /var/lib/postgresql/.tmux.conf
COPY ./config/.bashcfg.sh /var/lib/postgresql/.bashcfg.sh


## Optional: Set vim as default editor
ENV EDITOR=vim

## additional config on .bashrc
RUN echo '. /root/.bashcfg.sh' >> /root/.bashrc
RUN echo '. /var/lib/postgresql/.bashcfg.sh' >> /var/lib/postgresql/.bashrc

## Copy configuration files
## - Use postgres 16.11 config files
##   reasons:
##   1. FEHD needs older 16.X for compatibility with some extensions
##   2. 'transaction_timeout' is not supported in Postgres 16.11
COPY ./config/postgresql.16.11.conf /etc/postgresql/postgresql.conf
COPY ./config/pg_hba.conf /etc/postgresql/pg_hba.conf

## Set proper ownership and permissions
RUN chown postgres:postgres \
  /etc/postgresql/postgresql.conf \
  /etc/postgresql/pg_hba.conf
