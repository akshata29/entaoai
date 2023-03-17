import { useRef, useState, useEffect } from "react";
import { DefaultButton, Spinner } from "@fluentui/react";
import {
    Card,
    CardFooter,
  } from "@fluentui/react-components";
  import { Checkbox, ICheckboxProps } from '@fluentui/react/lib/Checkbox';

import { BarcodeScanner24Filled } from "@fluentui/react-icons";
import { BlobServiceClient } from "@azure/storage-blob";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';
import { Label } from '@fluentui/react/lib/Label';
import { Stack, IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { DefaultPalette } from '@fluentui/react/lib/Styling';
import { TextField } from '@fluentui/react/lib/TextField';

import styles from "./Upload.module.css";

import { useDropzone } from 'react-dropzone'

const containerName =`${import.meta.env.VITE_CONTAINER_NAME}`
const sasToken = `${import.meta.env.VITE_SAS_TOKEN}`
const storageAccountName = `${import.meta.env.VITE_STORAGE_NAME}`
const docGeneratorUrl = `${import.meta.env.VITE_DOCGENERATOR_URL}`
const delay = (ms:number) => new Promise(res => setTimeout(res, ms))

// <snippet_get_client>
const uploadUrl = `https://${storageAccountName}.blob.core.windows.net/?${sasToken}`;

const Upload = () => {
    const [files, setFiles] = useState<any>([])
    const [loading, setLoading] = useState(false)

    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [multipleDocs, setMultipleDocs] = useState(false);
    const [indexName, setIndexName] = useState('');
    const [uploadText, setUploadText] = useState('');

    const stackStyles: IStackStyles = {
      root: {
        background: DefaultPalette.white,
        height: 250,
      },
    };
    const stackItemStyles: IStackItemStyles = {
      root: {
        alignItems: 'left',
        background: DefaultPalette.white,
        color: DefaultPalette.white,
        display: 'flex',
        justifyContent: 'left',
      },
    };

    // Tokens definition
    const outerStackTokens: IStackTokens = { childrenGap: 5 };
    const innerStackTokens: IStackTokens = {
      childrenGap: 5,
      padding: 10,
    };

    const options = [
      {
        key: 'pinecone',
        text: 'Pinecone'
      },
      {
        key: 'redis',
        text: 'Redis Stack'
      }
    ]

    const { getRootProps, getInputProps } = useDropzone({
        multiple: false,
        maxSize: 100000000,
        accept: {
          'application/pdf': ['.pdf']
        },
        onDrop: acceptedFiles => {
          setFiles(acceptedFiles.map(file => Object.assign(file)))
        }
    })
    const renderFilePreview = (file: File ) => {
        if (file.type.startsWith('image')) {
          return <img width={38} height={38} alt={file.name} src={URL.createObjectURL(file)} />
        } else {
          return <BarcodeScanner24Filled/>
        }
    }
    
    const handleRemoveFile = (file: File ) => {
        const uploadedFiles = files
        //const filtered = uploadedFiles.filter(i => i.name !== file.name)
        const filtered = uploadedFiles.filter((i: { name: string; }) => i.name !== file.name)
        setFiles([...filtered])
    }

    const handleRemoveAllFiles = () => {
        setFiles([])
    }
    const fileList = files.map((file:File) => (
        <div>
          <div className='file-details'>
            <div className='file-preview'>{renderFilePreview(file)}</div>
            <div key={file.name}>
              {file.name}
              &nbsp;
                {Math.round(file.size / 100) / 10 > 1000
                  ? (Math.round(file.size / 100) / 10000).toFixed(1) + ' MB'
                  : (Math.round(file.size / 100) / 10).toFixed(1) + ' KB'}
            </div>
          </div>
          <DefaultButton onClick={() => handleRemoveFile(file)} disabled={loading ? true : false}>Remove File</DefaultButton>
        </div>
    ))

    const uploadFileToBlob = async (file: File) => {
        if (!file) return
    
        //Upload the PDF file to blob storage
    
        setLoading(true)
        setUploadText('Uploading and Indexing your document...')
        const blobServiceClient = new BlobServiceClient(uploadUrl)
        const containerClient = blobServiceClient.getContainerClient(containerName)
        const blockBlobClient = containerClient.getBlockBlobClient(file.name)
    
        // set mimetype as determined from browser with file upload control
        const options = { blobHTTPHeaders: { blobContentType: file.type } }
    
        const url =  docGeneratorUrl + '&indexType=' + selectedItem?.key

        const requestOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                values: [
                  {
                    recordId: 0,
                    data: {
                      text: ''
                    }
                  }
                ]
              })
        };
        // Wait 5 seconds for the file to be uploaded
        //await delay(5000)
    
        //Trigger the function to Mine the PDF
        await blockBlobClient.uploadData(file, options)
        .then(() => {
          setUploadText("File uploaded successfully.  Now indexing the document.")
          fetch(url, requestOptions)
          .then((response) => {
            if (response.ok) {
              setUploadText("Completed Successfully.  You can now search for your document.")
            }
            else {
              setUploadText("Failure to upload the document.")
            }
            setFiles([])
            setLoading(false)
          })
          .catch((error : string) => {
            setUploadText(error)
            setFiles([])
            setLoading(false)
          })
        })

    }

    const handleUploadFiles = async () => {
      // if (multipleDocs && index)
      // {
        
      // }
      files.forEach(async (element: File) => {
        await uploadFileToBlob(element)
      })
    }

    const onMultipleDocs = (ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean): void => {
        setMultipleDocs(!!checked);
    };

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedItem(item);
    };

    const onChangeFirstTextFieldValue = (event: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        setIndexName(newValue || '');
    };
   
    useEffect(() => {
      setSelectedItem(options[0])
    }, [])

    return (
        <div className={styles.chatAnalysisPanel}>
            <Stack enableScopedSelectors tokens={outerStackTokens}>
              <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                <Stack.Item grow={2} styles={stackItemStyles}>
                  <Label>Index Type</Label>
                  &nbsp;
                  <Dropdown
                      selectedKey={selectedItem ? selectedItem.key : undefined}
                      onChange={onChange}
                      defaultSelectedKey="pinecone"
                      placeholder="Select an Index Type"
                      options={options}
                      styles={dropdownStyles}
                  />
                </Stack.Item>
                <Stack.Item grow={2} styles={stackItemStyles}>
                  <Checkbox label="Multiple Documents" checked={multipleDocs} onChange={onMultipleDocs} />
                </Stack.Item>
                <Stack.Item grow={2} styles={stackItemStyles}>
                  <TextField disabled={!multipleDocs} errorMessage="" label="Index Name (for single file will default to filename)" />
                </Stack.Item>
              </Stack>
            </Stack>
            <div className={styles.commandsContainer}>
            </div>
            <div>
                <h2 className={styles.chatEmptyStateSubtitle}>Upload your PDF</h2>
                <h2 {...getRootProps({ className: 'dropzone' })}>
                    <input {...getInputProps()} />
                        Drop PDF file here or click to upload. (Max file size 100 MB)
                </h2>
                {files.length ? (
                    <Card>
                        {fileList}
                        <br/>
                        <CardFooter>
                            <DefaultButton onClick={handleRemoveAllFiles} disabled={loading ? true : false}>Remove All</DefaultButton>
                            <DefaultButton onClick={handleUploadFiles} disabled={loading ? true : false}>
                                <span>Upload Pdf</span>
                            </DefaultButton>
                        </CardFooter>
                    </Card>
                ) : null}
                <br/>
                {loading ? <div><span>Please wait, Uploading and Processing your file</span><Spinner/></div> : null}
                <hr />
                <h2 className={styles.chatEmptyStateSubtitle}>
                  <TextField disabled={true} label={uploadText} />
                </h2>
            </div>
        </div>
    );
};

export default Upload;
