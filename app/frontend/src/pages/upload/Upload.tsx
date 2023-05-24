import { useRef, useState, useEffect } from "react";
import { DefaultButton, Spinner, PrimaryButton } from "@fluentui/react";
import {
    Card,
    CardFooter,
  } from "@fluentui/react-components";
import { Checkbox } from '@fluentui/react/lib/Checkbox';
import { IStyleSet, ILabelStyles, IPivotItemProps, Pivot, PivotItem } from '@fluentui/react';
import { makeStyles } from "@fluentui/react-components";

import { BarcodeScanner24Filled } from "@fluentui/react-icons";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';
import { Label } from '@fluentui/react/lib/Label';
import { Stack, IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { DefaultPalette } from '@fluentui/react/lib/Styling';
import { TextField } from '@fluentui/react/lib/TextField';
import { processDoc, uploadFile, uploadBinaryFile, refreshIndex, verifyPassword } from "../../api";

import styles from "./Upload.module.css";

import { useDropzone } from 'react-dropzone'

const buttonStyles = makeStyles({
  innerWrapper: {
    columnGap: "15px",
    display: "flex",
  },
  outerWrapper: {
    display: "flex",
    flexDirection: "column",
    rowGap: "15px",
  },
});

const Upload = () => {
    const [files, setFiles] = useState<any>([])
    const [loading, setLoading] = useState(false)
    const [selectedPdf, setSelectedPdf] = useState<IDropdownOption>();
    const [optionsPdf, setOptionsPdf] = useState<any>([])
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; name:string; indexName:string; embedded:boolean}[]>();
    const [embedded, setEmbedded] = useState(false);
    const [indexNs, setIndexNs] = useState('');
    const [existingIndexName, setExistingIndexName] = useState('');
    const [selectedIndex, setSelectedIndex] = useState<string>();
      
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [multipleDocs, setMultipleDocs] = useState(false);
    const [existingIndex, setExistingIndex] = useState(false);

    const [indexName, setIndexName] = useState('');
    const [uploadText, setUploadText] = useState('');
    const [lastHeader, setLastHeader] = useState<{ props: IPivotItemProps } | undefined>(undefined);
    const [missingIndexName, setMissingIndexName] = useState(false)
    const [parsedWebUrls, setParsedWebUrls] = useState<String[]>([''])
    const [webPages, setWebPages] = useState('')

    const [selectedConnector, setSelectedConnector] = useState<IDropdownOption>();
    const [connectorOptions, setConnectorOptions] = useState<any>([])
    const [blobConnectionString, setBlobConnectionString] = useState('');
    const [blobContainer, setBlobContainer] = useState('');
    const [blobPrefix, setBlobPrefix] = useState('');
    const [blobName, setBlobName] = useState('');
    const [s3Bucket, setS3Bucket] = useState('');
    const [s3Key, setS3Key] = useState('');
    const [s3AccessKey, setS3AccessKey] = useState('');
    const [s3SecretKey, setS3SecretKey] = useState('');
    const [s3Prefix, setS3Prefix] = useState('');

    const [uploadPassword, setUploadPassword] = useState('');
    const [missingUploadPassword, setMissingUploadPassword] = useState(false)
    const [uploadError, setUploadError] = useState(false)

    const [selectedTextSplitterItem, setSelectedTextSplitterItem] = useState<IDropdownOption>();

    const textSplitterOptions = [
      {
        key: 'recursive',
        text: 'Recursive Character Text Splitter'
      },
      {
        key: 'tiktoken',
        text: 'Tik Token'
      },
      {
        key: 'nltk',
        text: 'NLTK Text Splitter'
      },
      {
        key: 'formrecognizer',
        text: 'Form Recognizer'
      }
    ]

    const connectors = [
      { key: 's3file', text: 'Amazon S3 File'},
      { key: 's3Container', text: 'Amazon S3 Container'},
      { key: 'rds', text: 'Amazon RDS' },
      { key: 'adlscontainer', text: 'Azure Blob Container' },
      { key: 'adlsfile', text: 'Azure Blob File' },
    ]


    const labelStyles: Partial<IStyleSet<ILabelStyles>> = {
      root: { marginTop: 10 },
    };
    
    const stackStyles: IStackStyles = {
      root: {
        height: 250,
      },
    };
    const stackItemStyles: IStackItemStyles = {
      root: {
        alignItems: 'left',
        display: 'flex',
        justifyContent: 'left',
      },
    };

    const bStyles = buttonStyles();

    // Tokens definition
    const outerStackTokens: IStackTokens = { childrenGap: 5 };
    const innerStackTokens: IStackTokens = {
      childrenGap: 5,
      padding: 10,
    };

    const embeddingOptions = [
      {
        key: 'azureopenai',
        text: 'Azure Open AI'
      },
      {
        key: 'openai',
        text: 'Open AI'
      }
      // {
      //   key: 'local',
      //   text: 'Local Embedding'
      // }
    ]

    const options = [
      {
        key: 'pinecone',
        text: 'Pinecone'
      },
      {
        key: 'redis',
        text: 'Redis Stack'
      },
      {
        key: 'cogsearch',
        text: 'Cognitive Search'
      },
      {
        key: 'cogsearchvs',
        text: 'Cognitive Search Vector Store'
      }
      // {
      //   key: 'chroma',
      //   text: 'Chroma'
      // }
      // ,
      // {
      //   key: 'weaviate',
      //   text: 'Weaviate'
      // }
    ]

    const { getRootProps, getInputProps } = useDropzone({
        multiple: true,
        maxSize: 100000000,
        accept: {
          'application/pdf': ['.pdf'],
          'application/word': ['.doc', '.docx'],
          'application/csv': ['.csv'],
          'text/plain': ['.txt']
        },
        onDrop: acceptedFiles => {
          setFiles(acceptedFiles.map(file => Object.assign(file)))
          setIndexName(acceptedFiles[0].name.split('.').slice(0, -1).join('.'));
        }
    })

    const renderFilePreview = (file: File ) => {
        if (file.type.startsWith('image')) {
          return <img width={38} height={38} alt={file.name} src={URL.createObjectURL(file)} />
        } else {
          return <BarcodeScanner24Filled/>
        }
    }
    
    const refreshBlob = async (indexT: string) => {
      const files = []
      const indexType = []
  
      //const blobs = containerClient.listBlobsFlat(listOptions)
      const blobs = await refreshIndex()       
      for (const blob of blobs.values) {
        // if (blob.embedded == "true")
        // {
          if (blob.indexType == indexT) {
            files.push({
              text: blob.indexName,
              key: blob.namespace
            })
          }
          indexType.push({
                  key:blob.namespace,
                  iType:blob.indexType,
                  name:blob.name,
                  indexName:blob.indexName,                  
                  embedded: blob.embedded = (blob.embedded == "true")
          })
        //}
      }
      var uniqFiles = files.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)
      setOptionsPdf(uniqFiles)

      const defaultKey = uniqFiles[0].key
      setSelectedPdf(uniqFiles[0])

      var uniqIndexType = indexType.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)

      for (const item of uniqIndexType) {
          if (item.key == defaultKey) {
              setSelectedIndex(item.iType)
              setExistingIndexName(item.indexName)
              if (existingIndex)
                setIndexName(item.indexName)
              setIndexNs(item.key)
              setEmbedded(item.embedded)
          }
      }
      if (!existingIndex) 
        setIndexName('')
      setIndexMapping(uniqIndexType)
    }

    const onChangePdf = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedPdf(item);
      const defaultKey = item?.key
      const defaultName = item?.text
      if (defaultKey == undefined || defaultKey == '') {
        indexMapping?.findIndex((item) => {
          if (item.indexName == defaultName) {
              setSelectedIndex(item.iType)
              setExistingIndexName(item.indexName)
              if (existingIndex)
                setIndexName(item.indexName)
              setIndexNs(item.key)
              setEmbedded(item.embedded)
          }
        })
        if (!existingIndex) 
          setIndexName('')
      }
      else {
        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                setSelectedIndex(item.iType)
                setExistingIndexName(item.indexName)
                if (existingIndex)
                  setIndexName(item.indexName)
                setIndexNs(item.key)
                setEmbedded(item.embedded)
            }
        })
        if (!existingIndex) 
          setIndexName('')
      }
    };


    const handleRemoveFile = (file: File ) => {
        const uploadedFiles = files
        //const filtered = uploadedFiles.filter(i => i.name !== file.name)
        const filtered = uploadedFiles.filter((i: { name: string; }) => i.name !== file.name)
        setFiles([...filtered])
    }

    const handleRemoveAllFiles = () => {
        setFiles([])
        setIndexName('')
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
    
    const handleUploadFiles = async () => {
      if (uploadPassword == '') {
        setMissingUploadPassword(true)
        return
      }

      if (files.length > 1) {
        setMultipleDocs(true)
        if (indexName == '') {
          setMissingIndexName(true)
          return
        }
      }

      if (existingIndex && existingIndexName == '') {
        setMissingIndexName(true)
        return
      }

      setLoading(true)
      await verifyPassword("upload", uploadPassword)
      .then(async (verifyResponse:string) => {
        if (verifyResponse == "Success") {
          setUploadText("Password verified")
          setUploadText('Uploading your document...')
          let count = 0
          await new Promise( (resolve) => {
          files.forEach(async (element: File) => {
            //await uploadFileToBlob(element)
            try {
              const formData = new FormData();
              formData.append('file', element);
    
              await uploadBinaryFile(formData, indexName)
            }
            finally
            {
              count += 1
              if (count == files.length) {
                resolve(element)
              }
            }
          })
          })
          setUploadText("File uploaded successfully.  Now indexing the document.")

          await processDoc(String(selectedItem?.key), "files", (files.length > 1 ? "true" : "false"), 
          existingIndex ? existingIndexName : indexName, files,
          blobConnectionString, blobContainer, blobPrefix, blobName,
          s3Bucket, s3Key, s3AccessKey, s3SecretKey, s3Prefix,
          existingIndex ? "true" : "false", existingIndex ? indexNs : '',
          String(selectedEmbeddingItem?.key), String(selectedTextSplitterItem?.key))
          .then((response:string) => {
            if (response == "Success") {
              setUploadText("Completed Successfully.  You can now search for your document.")
            }
            else {
              setUploadText(response)
            }
            setFiles([])
            setLoading(false)
            setMissingIndexName(false)
            setMultipleDocs(false)
            setIndexName('')
          })
          .catch((error : string) => {
            setUploadText(error)
            setFiles([])
            setLoading(false)
            setMissingIndexName(false)
            setMultipleDocs(false)
            setIndexName('')
          })
          refreshBlob(String(selectedItem?.key))
        }
        else {
          setUploadText(verifyResponse)
        }
      })
      .catch((error : string) => {
        setUploadText(error)
        setFiles([])
        setLoading(false)
        setMissingIndexName(false)
        setMultipleDocs(false)
        setIndexName('')
      })
      setLoading(false)
    }

    const onProcessWebPages = async () => {
      if (uploadPassword == '') {
        setMissingUploadPassword(true)
        return
      }

      if (existingIndex && existingIndexName == '') {
        setMissingIndexName(true)
        return
      }

      const processPage = parsedWebUrls.filter(function(e){return e})
      if (processPage?.length == 0) {
        setUploadText('Provide the list of URL to Process...')
        return
      } 
      else 
      {
        if (indexName == '') {
          setMissingIndexName(true)
          return
        }
        setLoading(true)
        await verifyPassword("upload", uploadPassword)
        .then(async (verifyResponse:string) => {
          if (verifyResponse == "Success") {
            setUploadText("Password verified")

            setUploadText('Uploading your document...')
    
            const fileContentsAsString = "Will Process the Webpage and index it with IndexName as " + indexName + " and the URLs are " + processPage
            await uploadFile(indexName + ".txt", fileContentsAsString, "text/plain")
            .then(async () => {
              setUploadText("File uploaded successfully.  Now indexing the document.")
              await processDoc(String(selectedItem?.key), "webpages", "false", existingIndex ? existingIndexName : indexName, 
              processPage, blobConnectionString,
              blobContainer, blobPrefix, blobName, s3Bucket, s3Key, s3AccessKey,
              s3SecretKey, s3Prefix, existingIndex ? "true" : "false", existingIndex ? indexNs : '',
              String(selectedEmbeddingItem?.key), String(selectedTextSplitterItem?.key))
              .then((response) => {
                if (response == "Success") {
                  setUploadText("Completed Successfully.  You can now search for your document.")
                }
                else {
                  setUploadText("Failure to upload the document.")
                  setUploadError(true)
                }
                setWebPages('')
                setParsedWebUrls([''])
                setLoading(false)
                setMissingIndexName(false)
                setIndexName('')
              })
              .catch((error : string) => {
                setUploadText(error)
                setUploadError(true)
                setWebPages('')
                setParsedWebUrls([''])
                setLoading(false)
                setMissingIndexName(false)
                setIndexName('')
              })
              refreshBlob(String(selectedItem?.key))
            })
          }
          else {
            setUploadText(verifyResponse)
          }
        })
        .catch((error : string) => {
          setUploadText(error)
          setUploadError(true)
          setWebPages('')
          setParsedWebUrls([''])
          setLoading(false)
          setMissingIndexName(false)
          setIndexName('')
        })
        setLoading(false)
      }
    }

    const onProcessConnectors = async () => {
      if (uploadPassword == '') {
        setMissingUploadPassword(true)
        return
      }
      if (indexName == '') {
        setMissingIndexName(true)
        return
      }
      if (blobConnectionString == '' && (selectedConnector?.key == 'adlsfile' || selectedConnector?.key == 'adlscontainer')) {
        setMissingIndexName(true)
        return
      }
      if (blobContainer == '' && (selectedConnector?.key == 'adlsfile' || selectedConnector?.key == 'adlscontainer')) {
        setMissingIndexName(true)
        return
      }
      if (blobName == '' && selectedConnector?.key == 'adlsfile') {
        setMissingIndexName(true)
        return
      }
      if (s3AccessKey == '' && (selectedConnector?.key == 's3file' || selectedConnector?.key == 's3container')) {
        setMissingIndexName(true)
        return
      }
      if (s3SecretKey == '' && (selectedConnector?.key == 's3file' || selectedConnector?.key == 's3container')) {
        setMissingIndexName(true)
        return
      }
      if (s3Bucket == '' && (selectedConnector?.key == 's3file' || selectedConnector?.key == 's3container')) {
        setMissingIndexName(true)
        return
      }
      if (s3Key == '' && (selectedConnector?.key == 's3file')) {
        setMissingIndexName(true)
        return
      }

      if (existingIndex && existingIndexName == '') {
        setMissingIndexName(true)
        return
      }

      setLoading(true)
      await verifyPassword("upload", uploadPassword)
        .then(async (verifyResponse:string) => {
          if (verifyResponse == "Success") {
            setUploadText("Password verified")

            setUploadText('Uploading your document...')
      
            const fileContentsAsString = "Will Process the connector document and index it with IndexName as " + indexName
            await uploadFile(indexName + ".txt", fileContentsAsString, "text/plain")
              .then(async () => {
                setUploadText("File uploaded successfully.  Now indexing the document.")
                setUploadText('Processing data from your connector...')
                await processDoc(String(selectedItem?.key), String(selectedConnector?.key), "false", existingIndex ? existingIndexName : indexName,
                '', blobConnectionString,
                blobContainer, blobPrefix, blobName, s3Bucket, s3Key, s3AccessKey,
                s3SecretKey, s3Prefix, existingIndex ? "true" : "false", existingIndex ? indexNs : '',
                String(selectedEmbeddingItem?.key), String(selectedTextSplitterItem?.key))  
                .then((response) => {
                  if (response == "Success") {
                    setUploadText("Completed Successfully.  You can now search for your document.")
                  }
                  else {
                    setUploadText("Failure to upload the document.")
                  }
                  setLoading(false)
                  setMissingIndexName(false)
                  setIndexName('')
                  setBlobConnectionString('')
                  setBlobContainer('')
                  setBlobPrefix('')
                  setBlobName('')
                  setS3Bucket('')
                  setS3Key('')
                  setS3AccessKey('')
                  setS3SecretKey('')
                  setS3Prefix('')
                  })
                .catch((error : string) => {
                  setUploadText(error)
                  setLoading(false)
                  setMissingIndexName(false)
                  setIndexName('')
                  setBlobConnectionString('')
                  setBlobContainer('')
                  setBlobPrefix('')
                  setBlobName('')
                  setS3Bucket('')
                  setS3Key('')
                  setS3AccessKey('')
                  setS3SecretKey('')
                  setS3Prefix('')
                })
                refreshBlob(String(selectedItem?.key))
              })
          }
          else {
            setUploadText(verifyResponse)
          }
      })
      .catch((error : string) => {
          setUploadText(error)
          setLoading(false)
          setMissingIndexName(false)
          setIndexName('')
          setBlobConnectionString('')
          setBlobContainer('')
          setBlobPrefix('')
          setBlobName('')
          setS3Bucket('')
          setS3Key('')
          setS3AccessKey('')
          setS3SecretKey('')
          setS3Prefix('')
      })
      setLoading(false)
    }

    const onMultipleDocs = (ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean): void => {
        setMultipleDocs(!!checked);
    };

    const onExistingIndex = (ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean): void => {
      setExistingIndex(!!checked);
      checked ? setIndexName(selectedPdf ? selectedPdf.text as string : optionsPdf[0].text as string) : setIndexName('')
    };

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedItem(item);
      refreshBlob(item?.key as string)
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedEmbeddingItem(item);
    };

    const onTextSplitterChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedTextSplitterItem(item);
    };

    const onChangeIndexName = (event: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        setIndexName(newValue || '');
    };
   
    const onWebPageChange = (ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
      let webPage = newValue?.split("\n")
      webPage = webPage == undefined ? [''] : webPage.filter(function(e){return e}); 
      setParsedWebUrls(webPage);
    };

    const onConnectorChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedConnector(item);
    };

    const onBlobConnectionString = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setBlobConnectionString(newValue || "");
    };
    
    const onBlobContainer = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setBlobContainer(newValue || "");
    };
    
    const onBlobPrefix = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setBlobPrefix(newValue || "");
    };

    const onUploadPassword = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setUploadPassword(newValue || "");
      if (newValue == '') {
        setMissingUploadPassword(true)
      }
      else {
        setMissingUploadPassword(false)
      }
    };

    const onBlobName = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setBlobName(newValue || "");
    };

    const onS3Bucket = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setS3Bucket(newValue || "");
    };
    
    const onS3Key = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setS3Key(newValue || "");
    };
    
    const onS3AccessKey = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setS3AccessKey(newValue || "");
    };

    const onS3SecretKey = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setS3SecretKey(newValue || "");
    };  
    
    const onS3Prefix = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setS3Prefix(newValue || "");
    };  

    useEffect(() => {
      setSelectedItem(options[0])
      setConnectorOptions(connectors)
      setSelectedConnector(connectors[0])
      refreshBlob(options[0].key as string)
      setSelectedEmbeddingItem(embeddingOptions[0])
      setSelectedTextSplitterItem(textSplitterOptions[0])
    }, [])

    return (
        <div className={styles.chatAnalysisPanel}>
            <Stack enableScopedSelectors tokens={outerStackTokens}>
              <Stack enableScopedSelectors  tokens={innerStackTokens}>
                <Stack.Item grow styles={stackItemStyles}>
                  <Label>Index Type</Label>
                  &nbsp;
                  <Dropdown
                      selectedKey={selectedItem ? selectedItem.key : undefined}
                      onChange={onChange}
                      defaultSelectedKey="pinecone"
                      placeholder="Select an Index Type"
                      options={options}
                      disabled={false}
                      styles={dropdownStyles}
                  />
                  &nbsp;
                  <Label>Embedding Model</Label>
                  &nbsp;
                  <Dropdown
                      selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                      onChange={onEmbeddingChange}
                      defaultSelectedKey="azureopenai"
                      placeholder="Select an Embedding Model"
                      options={embeddingOptions}
                      disabled={false}
                      styles={dropdownStyles}
                  />
                  &nbsp;
                  <Label>Upload Password:</Label>&nbsp;
                  <TextField onChange={onUploadPassword}
                      errorMessage={!missingUploadPassword ? '' : "Note - Upload Password is required for Upload Functionality"}/>
                  &nbsp;
                  <Checkbox boxSide="end" label="Existing Index?" checked={existingIndex} onChange={onExistingIndex} />
                  &nbsp;
                  {existingIndex ? (
                  <Dropdown
                      selectedKey={selectedPdf ? selectedPdf.key : undefined}
                      // eslint-disable-next-line react/jsx-no-bind
                      onChange={onChangePdf}
                      placeholder="Select an PDF"
                      options={optionsPdf}
                      styles={dropdownStyles}
                  />) : (<></>)}
                </Stack.Item>
                <Stack.Item grow styles={stackItemStyles}>
                <Label>Chunk Document using :</Label>
                  &nbsp;
                  <Dropdown
                      selectedKey={selectedTextSplitterItem ? selectedTextSplitterItem.key : undefined}
                      onChange={onTextSplitterChange}
                      defaultSelectedKey="azureopenai"
                      placeholder="Select text splitter"
                      options={textSplitterOptions}
                      disabled={false}
                      styles={dropdownStyles}
                  />
                </Stack.Item>
              </Stack>
            </Stack>
            <Pivot aria-label="Document Upload" onLinkClick={setLastHeader}>
              <PivotItem
                headerText="Files"
                headerButtonProps={{
                  'data-order': 1,
                }}
              >
                <Stack enableScopedSelectors tokens={outerStackTokens}>
                  <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                    <Stack.Item grow={2} styles={stackItemStyles}>
                      <Checkbox label="Multiple Documents" checked={multipleDocs} onChange={onMultipleDocs} />
                    </Stack.Item>
                    <Stack.Item grow={2} styles={stackItemStyles}>
                      <TextField onChange={onChangeIndexName} value={indexName}
                          errorMessage={!missingIndexName ? '' : "Index name is required"}
                          label="Index Name" />
                    </Stack.Item>
                  </Stack>
                </Stack>
                <div className={styles.commandsContainer}>
                </div>
                <div>
                    <h2 className={styles.chatEmptyStateSubtitle}>Upload your PDF/text/CSV/Word Document file</h2>
                    <h2 {...getRootProps({ className: 'dropzone' })}>
                        <input {...getInputProps()} />
                            Drop PDF/text/CSV/Word Document file here or click to upload. (Max file size 100 MB)
                    </h2>
                    {files.length ? (
                        <Card>
                            {fileList}
                            <br/>
                            <CardFooter>
                                <DefaultButton onClick={handleRemoveAllFiles} disabled={loading ? true : false}>Remove All</DefaultButton>
                                <DefaultButton onClick={handleUploadFiles} disabled={loading ? true : false}>
                                    <span>Upload File</span>
                                </DefaultButton>
                            </CardFooter>
                        </Card>
                    ) : null}
                    <br/>
                    {loading ? <div><span>Please wait, Uploading and Processing your file</span><Spinner/></div> : null}
                    <hr />
                    <h2 className={styles.chatEmptyStateSubtitle}>
                      <TextField disabled={true} label={uploadError ? '' : uploadText} errorMessage={!uploadError ? '' : uploadText} />
                    </h2>
                </div>
              </PivotItem>
              <PivotItem headerText="Web Pages">
                <Stack enableScopedSelectors tokens={outerStackTokens}>
                  <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                    <Stack.Item grow={2} styles={stackItemStyles}>
                      <TextField onChange={onWebPageChange} multiline autoAdjustHeight styles={{root: {width: '700px'}}}
                          label="List of Urls (followed by newline)"
                          defaultValue=""
                          />
                    </Stack.Item>
                    <Stack.Item grow>
                    <TextField onChange={onChangeIndexName} 
                          styles={{root: {width: '400px'}}}
                          errorMessage={!missingIndexName ? '' : "Index name is required"}
                          value = {indexName}
                          label="Index Name" />
                    </Stack.Item>
                    <Stack.Item grow>
                        <PrimaryButton text="Process Pages" onClick={onProcessWebPages}  />
                        <h2 className={styles.chatEmptyStateSubtitle}>
                          <TextField disabled={true} label={uploadText} />
                        </h2>
                    </Stack.Item>
                  </Stack>
                </Stack>
              </PivotItem>
              <PivotItem headerText="Connectors">
                <Stack enableScopedSelectors tokens={outerStackTokens}>
                  <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                    <Stack.Item grow={2} styles={stackItemStyles}>
                        <Dropdown
                            selectedKey={selectedConnector ? selectedConnector.key : undefined}
                            // eslint-disable-next-line react/jsx-no-bind
                            onChange={onConnectorChange}
                            placeholder="Select an Connector"
                            options={connectorOptions}
                            styles={dropdownStyles}
                        />
                        <h4 className={styles.chatEmptyStateSubtitle}>
                          Note : Currently only PDF files are supported from cloud storage services
                        </h4>
                    </Stack.Item>
                    <Stack.Item>
                      <TextField onChange={onChangeIndexName} 
                          styles={{root: {width: '400px'}}}
                          errorMessage={!missingIndexName ? '' : "Index name is required"}
                          value = {indexName}
                          label="Index Name" />
                    </Stack.Item>
                    <Stack.Item grow>
                    {(selectedConnector?.key === 'adlscontainer' || selectedConnector?.key === 'adlsfile') && (
                        <div>
                          <TextField onChange={onBlobConnectionString} 
                            styles={{root: {width: '700px'}}}
                            errorMessage={!missingIndexName ? '' : "Connection String is required"}
                            value = {blobConnectionString}
                            label="Connection String" />
                          <div>
                            <TextField onChange={onBlobContainer} 
                              styles={{root: {width: '200px'}}}
                              errorMessage={!missingIndexName ? '' : "Container Name required"}
                              value = {blobContainer}
                              label="Container Name" />
                          </div>
                        </div>
                    )}
                    {(selectedConnector?.key === 'adlscontainer') && (
                        <div>
                          <TextField onChange={onBlobPrefix} 
                              styles={{root: {width: '150px'}}}
                              value = {blobPrefix}
                              label="Prefix Name" />
                        </div>
                    )}
                    {(selectedConnector?.key === 'adlsfile') && (
                        <div>
                          <TextField onChange={onBlobName} 
                              styles={{root: {width: '450px'}}}
                              value = {blobName}
                              errorMessage={!missingIndexName ? '' : "Blob Name required"}
                              label="Blob Name" />
                        </div>
                    )}
                    {(selectedConnector?.key === 's3file' || selectedConnector?.key === 's3Container') && (
                        <div>
                          <TextField onChange={onS3Bucket} 
                            styles={{root: {width: '200px'}}}
                            errorMessage={!missingIndexName ? '' : "S3 Bucket is required"}
                            value = {s3Bucket}
                            label="S3 Bucket" />
                          <div>
                            <TextField onChange={onS3AccessKey} 
                              styles={{root: {width: '300px'}}}
                              errorMessage={!missingIndexName ? '' : "S3 Access Key required"}
                              value = {s3AccessKey}
                              label="S3 Access Key" />
                            <TextField onChange={onS3SecretKey} 
                              styles={{root: {width: '400px'}}}
                              errorMessage={!missingIndexName ? '' : "S3 Secret Key required"}
                              value = {s3SecretKey}
                              label="S3 Secret Key" />
                          </div>
                        </div>
                    )}
                    {(selectedConnector?.key === 's3Container') && (
                        <div>
                          <TextField onChange={onS3Prefix} 
                              styles={{root: {width: '150px'}}}
                              value = {s3Prefix}
                              label="Prefix Name" />
                        </div>
                    )}
                    {(selectedConnector?.key === 's3file') && (
                        <div>
                          <TextField onChange={onS3Key} 
                              styles={{root: {width: '450px'}}}
                              value = {s3Key}
                              errorMessage={!missingIndexName ? '' : "S3 Key is required"}
                              label="S3 Key" />
                        </div>
                    )}
                    </Stack.Item>
                    <Stack.Item grow>
                        <PrimaryButton text="Process Documents" onClick={onProcessConnectors}  />
                        <h2 className={styles.chatEmptyStateSubtitle}>
                          <TextField disabled={true} label={uploadText} />
                        </h2>
                    </Stack.Item>
                  </Stack>
                </Stack>
              </PivotItem>
              {/* <PivotItem headerText="iFixIt Manuals">
              </PivotItem> */}
            </Pivot>
        </div>
    );
};

export default Upload;
