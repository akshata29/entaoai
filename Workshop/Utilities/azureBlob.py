from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas
from datetime import datetime, timedelta
import logging
import tempfile, os

def upsertMetadata(connectionString, container, fileName, metadata):
    try:
        blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
        containerClient = blobServiceClient.get_container_client(container)
        blobClient = containerClient.get_blob_client(fileName)
        blobMetadata = blobClient.get_blob_properties().metadata
        blobMetadata.update(metadata)
        logging.info("Upserting metadata for file: " + fileName + " Metadata: " + str(blobMetadata))
        blobClient.set_blob_metadata(metadata=blobMetadata)
    except Exception as e:
        logging.info("Error upserting metadata for file: " + fileName + " Error: " + str(e))
        pass

def getBlob(connectionString, container, fileName):
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    blobClient = blobServiceClient.get_blob_client(container=container, blob=fileName)
    readBytes = blobClient.download_blob().readall()

    return readBytes

def getAllBlobs(connectionString, container):
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    # Get files in the container
    containerClient = blobServiceClient.get_container_client(container)
    blobList = containerClient.list_blobs(include='metadata')

    return blobList

def getFullPath(connectionString, container, fileName):
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    blobClient = blobServiceClient.get_blob_client(container=container, blob=fileName)
    return blobClient.url

def getLocalBlob(connectionString, container, fileName, indexNs):
    if (indexNs != None):
        blobList = getAllBlobs(connectionString, container)
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
    readBytes  = getBlob(connectionString, container, fileName)
    os.makedirs(os.path.dirname(tempfile.gettempdir()), exist_ok=True)
    try:
        with open(downloadPath, "wb") as file:
            file.write(readBytes)
    except Exception as e:
        logging.error(e)

    logging.info("File created " + downloadPath)
    return downloadPath

def getSasToken(connectionString, container, fileName):
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    blobClient = blobServiceClient.get_blob_client(container=container, blob=fileName)
    sasToken = blobClient.url + '?' + generate_blob_sas(account_name=blobClient.account_name, container_name=container, blob_name=fileName,
       account_key=blobClient.credential.account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3)
    )
    return sasToken

def copyS3Blob(downloadPath, blobName, openAiBlobConnectionString, openAiBlobContainer):
    with open(downloadPath, "wb") as file:
        readBytes = file.read()
    blobServiceClient = BlobServiceClient.from_connection_string(openAiBlobConnectionString)
    blobClient = blobServiceClient.get_blob_client(container=openAiBlobContainer, blob=blobName)
    blobClient.upload_blob(readBytes,overwrite=True)

def copyBlob(blobConnectionString, blobContainer, blobName, openAiBlobConnectionString, openAiBlobContainer):
    readBytes  = getBlob(blobConnectionString, blobContainer, blobName)
    blobServiceClient = BlobServiceClient.from_connection_string(openAiBlobConnectionString)
    blobClient = blobServiceClient.get_blob_client(container=openAiBlobContainer, blob=blobName)
    blobClient.upload_blob(readBytes,overwrite=True)

def uploadBlob(connectionString, container, fileName, fileContent, contentType):
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    blobClient = blobServiceClient.get_blob_client(container=container, blob=fileName)
    blobClient.upload_blob(fileContent,overwrite=True, content_settings=ContentSettings(content_type=contentType))
