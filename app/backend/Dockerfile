FROM mcr.microsoft.com/azure-functions/python:4-python3.11

RUN apt-get update

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /home/site/wwwroot

COPY . /home/site/wwwroot

EXPOSE 80
#CMD python app.py
CMD [ "python", "app.py"]
#CMD [ "python", "-m" , "flask", "run", "--host=0.0.0.0"]