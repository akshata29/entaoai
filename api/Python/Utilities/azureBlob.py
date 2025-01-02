from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas
from datetime import datetime, timedelta
import logging
import tempfile, os
from azure.identity import ClientSecretCredential, DefaultAzureCredential

def upsertMetadata(tenantId, clientId, clientSecret, blobAccountName, container, fileName, metadata):
    try:
        credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
        blobService = BlobServiceClient(
                "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
        containerClient = blobService.get_container_client(container)
        blobClient = containerClient.get_blob_client(fileName)
        blobMetadata = blobClient.get_blob_properties().metadata
        blobMetadata.update(metadata)
        logging.info("Upserting metadata for file: " + fileName + " Metadata: " + str(blobMetadata))
        blobClient.set_blob_metadata(metadata=blobMetadata)
    except Exception as e:
        logging.info("Error upserting metadata for file: " + fileName + " Error: " + str(e))
        pass

def getBlob(tenantId, clientId, clientSecret, blobAccountName, container, fileName):
    credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
    blobService = BlobServiceClient(
            "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
    blobClient = blobService.get_blob_client(container, blob=fileName)
    readBytes = blobClient.download_blob().readall()

    return readBytes

def getAllBlobs(tenantId, clientId, clientSecret, blobAccountName, container):
    credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
    blobServiceClient = BlobServiceClient(
            "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
    # Get files in the container
    containerClient = blobServiceClient.get_container_client(container)
    blobList = containerClient.list_blobs(include='metadata')

    return blobList

def getFullPath(tenantId, clientId, clientSecret, blobAccountName, container, fileName):
    credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
    blobServiceClient = BlobServiceClient(
            "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
    blobClient = blobServiceClient.get_blob_client(container=container, blob=fileName)
    return blobClient.url

def getLocalBlob(tenantId, clientId, clientSecret, blobAccountName, container, fileName, indexNs):
    if (indexNs != None):
        blobList = getAllBlobs(tenantId, clientId, clientSecret, blobAccountName, container)
        for file in blobList:
            if file.metadata["embedded"] == "true":
                namespace = file.metadata["namespace"]
                if namespace == indexNs:
                    fileName = file.name
                    break
    downloadPath = os.path.join(tempfile.gettempdir(), fileName)
    if (os.path.exists(downloadPath)):
        logging.info("File already exists " + downloadPath)
        return downloadPath
    readBytes  = getBlob(tenantId, clientId, clientSecret, blobAccountName, container, fileName)
    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
    try:
        with open(downloadPath, "wb") as file:
            file.write(readBytes)
    except Exception as e:
        logging.error(e)

    logging.info("File created " + downloadPath)
    return downloadPath

def copyS3Blob(tenantId, clientId, clientSecret, blobAccountName, downloadPath, blobName, openAiBlobContainer):
    with open(downloadPath, "wb") as file:
        readBytes = file.read()
    credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
    blobService = BlobServiceClient(
            "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
    blobClient = blobService.get_blob_client(container=openAiBlobContainer, blob=blobName)
    blobClient.upload_blob(readBytes,overwrite=True)

def copyBlob(tenantId, clientId, clientSecret, blobAccountName, blobContainer, blobName, openAiBlobContainer):
    readBytes  = getBlob(tenantId, clientId, clientSecret, blobAccountName, blobContainer, blobName)
    credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
    blobService = BlobServiceClient(
            "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
    blobClient = blobService.get_blob_client(openAiBlobContainer, blob=blobName)
    blobClient.upload_blob(readBytes,overwrite=True)

def deleteBlob(tenantId, clientId, clientSecret, blobAccountName, container, fileName):
    credentials = ClientSecretCredential(tenantId, clientId, clientSecret)
    blobService = BlobServiceClient(
            "https://{}.blob.core.windows.net".format(blobAccountName), credential=credentials)
    blobClient = blobService.get_blob_client(container, blob=fileName)
    blobClient.delete_blob()