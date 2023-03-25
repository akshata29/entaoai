from azure.storage.blob import BlobServiceClient, ContentSettings

def upsertMetadata(connectionString, container, fileName, metadata):
    blobClient = BlobServiceClient.from_connection_string(connectionString).get_blob_client(container=container, blob=fileName)
    blob_metadata = blobClient.get_blob_properties().metadata
    blob_metadata.update(metadata)
    blobClient.set_blob_metadata(metadata= blob_metadata)

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

def uploadBlob(connectionString, container, fileName, fileContent, contentType):
    blobServiceClient = BlobServiceClient.from_connection_string(connectionString)
    blobClient = blobServiceClient.get_blob_client(container=container, blob=fileName)
    blobClient.upload_blob(fileContent,overwrite=True, content_settings=ContentSettings(content_type=contentType))
