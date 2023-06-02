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
import { AskResponse, processSummary, uploadSummaryBinaryFile, verifyPassword } from "../../api";

import styles from "./Summary.module.css";

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

const Summary = () => {
    const [files, setFiles] = useState<any>([])
    const [loading, setLoading] = useState(false)
    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [multipleDocs, setMultipleDocs] = useState(false);
    const [uploadText, setUploadText] = useState('');
    const [uploadPassword, setUploadPassword] = useState('');
    const [missingUploadPassword, setMissingUploadPassword] = useState(false)
    const [uploadError, setUploadError] = useState(false)
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();
    const [summaryText, setsummaryText] = useState('');
    const [intermediateStepsText, setIntermediateStepsText] = useState<string[]>();

    const chainTypeOptions = [
      { key: 'stuff', text: 'Stuff'},
      { key: 'map_reduce', text: 'Map Reduce' },
      { key: 'refine', text: 'Refine'},
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

    const { getRootProps, getInputProps } = useDropzone({
        multiple: true,
        maxSize: 100000000,
        accept: {
          'application/pdf': ['.pdf'],
          'application/word': ['.doc', '.docx'],
          'application/csv': ['.csv'],
          'application/json': ['.json'],
          'text/plain': ['.txt']
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
    
    const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedChain(item);
    };

    const handleUploadFiles = async () => {
      if (uploadPassword == '') {
        setMissingUploadPassword(true)
        return
      }

      if (files.length > 1) {
        setMultipleDocs(true)
      }

      setsummaryText('')
      setIntermediateStepsText([])
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
    
              await uploadSummaryBinaryFile(formData)
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

          await processSummary("files", (files.length > 1 ? "true" : "false"), 
          files, String(selectedEmbeddingItem?.key), String(selectedChain?.key))
          .then((response:AskResponse) => {
            setUploadText("Document summary successfully completed.")
            setIntermediateStepsText(response.data_points)
            setsummaryText(response.answer)
            setFiles([])
            setLoading(false)
            setMultipleDocs(false)
          })
          .catch((error : string) => {
            setUploadText(error)
            setFiles([])
            setLoading(false)
            setMultipleDocs(false)
          })
        }
        else {
          setUploadText(verifyResponse)
        }
      })
      .catch((error : string) => {
        setUploadText(error)
        setFiles([])
        setLoading(false)
        setMultipleDocs(false)
      })
      setLoading(false)
    }

    const onMultipleDocs = (ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean): void => {
        setMultipleDocs(!!checked);
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedEmbeddingItem(item);
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

    useEffect(() => {
      setSelectedEmbeddingItem(embeddingOptions[0])
      setSelectedChain(chainTypeOptions[0])
    }, [])

    return (
        <div className={styles.chatAnalysisPanel}>
            <Stack enableScopedSelectors tokens={outerStackTokens}>
              <Stack enableScopedSelectors  tokens={innerStackTokens}>
                <Stack.Item grow styles={stackItemStyles}>
                  <Label>Embedding Model</Label>
                  &nbsp;
                  <Dropdown
                      selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                      onChange={onEmbeddingChange}
                      placeholder="Select an Embedding Model"
                      options={embeddingOptions}
                      disabled={false}
                      styles={dropdownStyles}
                  />
                  &nbsp;
                  <Label>Chain Type</Label>
                  &nbsp;
                  <Dropdown 
                      onChange={onChainChange}
                      selectedKey={selectedChain ? selectedChain.key : 'stuff'}
                      options={chainTypeOptions}
                      disabled={false}
                      styles={dropdownStyles}
                  />
                  &nbsp;
                  <Label>Upload Password:</Label>&nbsp;
                  <TextField onChange={onUploadPassword}
                      errorMessage={!missingUploadPassword ? '' : "Note - Upload Password is required for Upload Functionality"}/>
                </Stack.Item>
              </Stack>
            </Stack>
            <Stack enableScopedSelectors tokens={outerStackTokens}>
              {/* <Stack.Item grow={2} styles={stackItemStyles}>
                <Checkbox label="Multiple Documents" checked={multipleDocs} onChange={onMultipleDocs} />
              </Stack.Item> */}
            <Stack.Item grow={2} styles={stackItemStyles}>
              <div className={styles.commandsContainer}>
              </div>
              <div>
                  <h2 className={styles.chatEmptyStateSubtitle}>Upload your PDF/text/CSV/JSON/Word Document file</h2>
                  <h2 {...getRootProps({ className: 'dropzone' })}>
                      <input {...getInputProps()} />
                          Drop PDF/text/CSV/JSON/Word Document file here or click to upload. (Max file size 100 MB)
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
              </Stack.Item>
            </Stack>
            <Stack.Item grow={2} styles={stackItemStyles}>
              <Label>Summary&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</Label>
              {/* <TextField style={{ resize: 'none', width: '750px', height: '500px' }} disabled={false} multiline={true}/> */}
              <textarea
                    style={{ resize: 'none', width: '100%', height: '500px' }}
                    value={summaryText}
                    disabled={false}
              />
            </Stack.Item>
            <br/>
            <Stack.Item grow={2} styles={stackItemStyles}>
              <Label>Summary List</Label>
              <textarea
                    style={{ resize: 'none', width: '100%', height: '500px' }}
                    value={intermediateStepsText}
                    disabled={false}
              />
            </Stack.Item>
        </div>
    );
};

export default Summary;
