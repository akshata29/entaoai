FROM mcr.microsoft.com/azureml/promptflow/promptflow-runtime:20230829.v3
COPY * ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -r extra_requirements.txt
