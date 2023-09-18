FROM mcr.microsoft.com/azureml/promptflow/promptflow-runtime:20230829.v3

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ODBC
# adding custom MS repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
#RUN curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# install SQL Server drivers
# install SQL Server tools
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18
RUN echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
RUN /bin/bash -c "source ~/.bashrc"

RUN apt-get install -y unixodbc-dev=2.3.11-1

## Install dbcopilot
COPY ./extra_requirements.txt ./
RUN pip install -r extra_requirements.txt