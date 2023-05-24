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
import { DefaultPalette, EdgeChromiumHighContrastSelector } from '@fluentui/react/lib/Styling';
import { TextField } from '@fluentui/react/lib/TextField';
import { verifyPassword, refreshIndex, AskResponse, indexManagement } from "../../api";

import styles from "./Admin.module.css";

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

const Admin = () => {
    const [files, setFiles] = useState<any>([])
    const [loading, setLoading] = useState(false)

    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const [selectedIndexType, setSelectedIndexType] = useState<IDropdownOption>();

    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [indexName, setIndexName] = useState('');
    const [indexNs, setIndexNs] = useState('');

    const [blobName, setBlobName] = useState('');
    const [uploadText, setUploadText] = useState('');
    const [lastHeader, setLastHeader] = useState<{ props: IPivotItemProps } | undefined>(undefined);

    const [adminPassword, setAdminPassword] = useState('');
    const [missingAdminPassword, setMissingAdminPassword] = useState(false)
    const [uploadError, setUploadError] = useState(false)
    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [embedded, setEmbedded] = useState(false);
    const [summary, setSummary] = useState<string>();
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; name:string; indexName:string; 
      summary:string; qa:string; embedded:boolean}[]>();
    const [options, setOptions] = useState<any>([])


    const labelStyles: Partial<IStyleSet<ILabelStyles>> = {
      root: { marginTop: 10 },
    };
    
    const stackStyles: IStackStyles = {
      root: {
        // background: DefaultPalette.white,
        height: 250,
      },
    };
    const stackItemStyles: IStackItemStyles = {
      root: {
        alignItems: 'left',
        // background: DefaultPalette.white,
        // color: DefaultPalette.white,
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

    const indexOptions = [
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
                  summary:blob.summary,
                  qa:blob.qa,
                  embedded: blob.embedded = (blob.embedded == "true")
          })
        //}
      }
      var uniqFiles = files.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)
      setOptions(uniqFiles)

      const defaultKey = uniqFiles[0].key
      setSelectedItem(uniqFiles[0])

      var uniqIndexType = indexType.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)

      for (const item of uniqIndexType) {
          if (item.key == defaultKey) {
              setSelectedIndex(item.iType)
              setSummary(item.summary)
              setBlobName(item.name)
              setIndexName(item.indexName)
              setIndexNs(item.key)
              setEmbedded(item.embedded)
          }
      }
      setIndexMapping(uniqIndexType)
    }

    const onDeleteIndex = async () => {
      if (adminPassword == '') {
        setMissingAdminPassword(true)
        return
      }

      await verifyPassword("admin", adminPassword)
        .then(async (verifyResponse:string) => {
          if (verifyResponse == "Success") {
            setUploadText("Password verified")
            setLoading(true)
            setUploadText('Deleting your Index...')

            await indexManagement(String(selectedIndexType?.key), indexName, blobName, indexNs, "delete")  
              .then((response:string) => {
                if (response == "Success") {
                  setUploadText("Index Deleted Successfully")
                }
                else {
                  setUploadText("Failure to delete the index.")
                }
                setLoading(false)
                })
              .catch((error : string) => {
                setUploadText(error)
                setLoading(false)
              })
              refreshBlob(String(selectedIndexType?.key))
          }
          else {
            setUploadText(verifyResponse)
          }
      })
      .catch((error : string) => {
          setUploadText(error)
          setLoading(false)
      })
    }

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedItem(item);
      const defaultKey = item?.key
      const defaultName = item?.text
      if (defaultKey == undefined || defaultKey == '') {
        indexMapping?.findIndex((item) => {
          if (item.indexName == defaultName) {
              setSelectedIndex(item.iType)
              setSummary(item.summary)
              setBlobName(item.name)
              setIndexName(item.indexName)
              setIndexNs(item.key)
              setEmbedded(item.embedded)
          }
        })
      }
      else {
        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                setSelectedIndex(item.iType)
                setSummary(item.summary)
                setBlobName(item.name)
                setIndexName(item.indexName)
                setIndexNs(item.key)
                setEmbedded(item.embedded)
            }
        })
      }
    };

    const onIndexTypeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedIndexType(item);
      refreshBlob(String(item?.key))
    };

    const onAdminPassword = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
      setAdminPassword(newValue || "");
      if (newValue == '') {
        setMissingAdminPassword(true)
      }
      else {
        setMissingAdminPassword(false)
      }
    };

    useEffect(() => {
      setSelectedIndexType(indexOptions[0])
      refreshBlob("pinecone")
    }, [])

    return (
        <div className={styles.chatAnalysisPanel}>
            <Stack enableScopedSelectors tokens={outerStackTokens}>
              <Stack enableScopedSelectors  tokens={innerStackTokens}>
                <Stack.Item grow styles={stackItemStyles}>
                  <Label>Admin Password:</Label>&nbsp;
                  <TextField onChange={onAdminPassword}
                      errorMessage={!missingAdminPassword ? '' : "Note - Admin Password is required for Admin Functionality"}/>
                </Stack.Item>
              </Stack>
            </Stack>
            <Pivot aria-label="Admin" onLinkClick={setLastHeader}>
              <PivotItem headerText="Index Management">
                <Stack enableScopedSelectors tokens={outerStackTokens}>
                  <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                    <Stack.Item grow={2} styles={stackItemStyles}>
                      <Label>Index Type</Label>
                      &nbsp;
                      <Dropdown
                          selectedKey={selectedIndexType ? selectedIndexType.key : undefined}
                          onChange={onIndexTypeChange}
                          defaultSelectedKey="pinecone"
                          placeholder="Select an Index Type"
                          options={indexOptions}
                          disabled={false}
                          styles={dropdownStyles}
                      />
                      &nbsp;
                      <Dropdown
                          selectedKey={selectedItem ? selectedItem.key : undefined}
                          // eslint-disable-next-line react/jsx-no-bind
                          onChange={onChange}
                          placeholder="Select an PDF"
                          options={options}
                          styles={dropdownStyles}
                      />
                    </Stack.Item>
                    <Stack.Item grow>
                      <TextField
                            className={styles.oneshotSettingsSeparator}
                            value={summary}
                            label="Summary"
                            multiline
                            autoAdjustHeight
                            readOnly
                            disabled={true}
                        />
                        &nbsp;
                      <TextField
                            className={styles.oneshotSettingsSeparator}
                            value={indexNs}
                            label="Namespace"
                            autoAdjustHeight
                            readOnly
                            disabled={true}
                        />
                      <Checkbox label="Embedded" checked={embedded} disabled />
                    </Stack.Item>
                    <Stack.Item grow>
                      <PrimaryButton text="Delete Index" onClick={onDeleteIndex}  />
                        <h2 className={styles.chatEmptyStateSubtitle}>
                          <TextField disabled={true} label={uploadText} />
                        </h2>
                    </Stack.Item>
                  </Stack>
                </Stack>
              </PivotItem>
            </Pivot>
        </div>
    );
};

export default Admin;
