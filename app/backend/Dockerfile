FROM python:3.9

RUN apt-get update

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

WORKDIR /home/site/wwwroot

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /home/site/wwwroot

EXPOSE 80
CMD python app.py
