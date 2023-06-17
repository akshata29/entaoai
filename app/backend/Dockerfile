FROM python:3.9

RUN apt-get update

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
COPY azure_search_documents-11.4.0b4-py3-none-any.whl /
RUN pip install -r /requirements.txt

WORKDIR /home/site/wwwroot

COPY . /home/site/wwwroot

EXPOSE 80
CMD python app.py
