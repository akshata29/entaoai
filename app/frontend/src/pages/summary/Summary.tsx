import { useState, useEffect, useMemo } from "react";
import { Spinner, PrimaryButton, DefaultButton, TextField } from "@fluentui/react";
import { makeStyles } from "@fluentui/react-components";

import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';
import { Label } from '@fluentui/react/lib/Label';
import { Stack, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { AskRequest, Approaches, processSummary, refreshIndex } from "../../api";
import { DetailsList, DetailsListLayoutMode, SelectionMode, Selection} from '@fluentui/react/lib/DetailsList';

import styles from "./Summary.module.css";

const Summary = () => {
  const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
  const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
  const [selectedChain, setSelectedChain] = useState<IDropdownOption>();
  const [selectedDocument, setSelectedDocument] = useState<string>('')
  const [selectedProspectus, setSelectedProspectus] = useState<IDropdownOption>();
  const [selectedSummaryTopicItem, setSelectedSummaryTopicItem] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<unknown>();
  const [selectedItems, setSelectedItems] = useState<any[]>([]);
  const [summaryQuestions, setSummaryQuestions] = useState<any>();
  const [options, setOptions] = useState<any>([])
  const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
  const [selectedIndex, setSelectedIndex] = useState<string>();
  const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string;  summary:string; qa:string; chunkSize:string; chunkOverlap:string; promptType:string, singleFile:boolean, fileName:string}[]>();
  const [selectedPromptTypeItem, setSelectedPromptTypeItem] = useState<IDropdownOption>();
  const [promptTemplate, setPromptTemplate] = useState<string>("");
  const [customTopic, setCustomTopic] = useState<string>("");
  const [selectedDeploymentType, setSelectedDeploymentType] = useState<IDropdownOption>();
  const [selectedChunkSize, setSelectedChunkSize] = useState<string>()

  const dropdownShortStyles: Partial<IDropdownStyles> = { dropdown: { width: 200 } };

  const deploymentTypeOptions = [
    {
      key: 'gpt35',
      text: 'GPT 3.5 Turbo'
    },
    {
      key: 'gpt3516k',
      text: 'GPT 3.5 Turbo - 16k'
    }
  ]

  const chainTypeOptions = [
    { key: 'stuff', text: 'Stuff'},
    { key: 'map_reduce', text: 'Map Reduce' },
    { key: 'refine', text: 'Refine'},
  ]

  const summaryTopicOptions = [
    {
      key: 'Strengths',
      text: 'Strengths'
    },
    {
      key: 'Growth Strategy',
      text: 'Growth Strategy'
    },
    {
      key: 'Investment Risk',
      text: 'Investment Risk'
    },
    {
      key: 'Organization Structure',
      text: 'Organization Structure'
    },
    {
        key: 'Risk Factors',
        text: 'Risk Factors'
    },
    {
        key: 'IPO Offering',
        text: 'IPO Offering'
    },
    {
        key: 'Financial Data',
        text: 'Financial Data'
    },
    {
        key: 'Key Operating Metrics',
        text: 'Key Operating Metrics'
    },
    {
        key: 'Business Overview',
        text: 'Business Overview'
    },
    {
        key: 'Success Stories',
        text: 'Success Stories'
    },
    {
        key: 'Intellectual Property',
        text: 'Intellectual Property'
    },
    {
        key: 'Capital Stock',
        text: 'Capital Stock'
    },
    {
        key: 'Stockholder Agreements',
        text: 'Stockholder Agreements'
    },
    {
        key: 'Underwriting',
        text: 'Underwriting'
    }
  ]

  const summaryColumns = [
    {
      key: 'Question',
      name: 'Question or Topic',
      fieldName: 'question',
      minWidth: 400, maxWidth: 400, isResizable: false, isMultiline: true
    },
    {
      key: 'Answer',
      name: 'Answer or Summarization',
      fieldName: 'answer',
      minWidth: 700, maxWidth: 900, isResizable: false, isMultiline: true
    }
  ]

  const stackItemStyles: IStackItemStyles = {
      root: {
          alignItems: 'left',
          // background: DefaultPalette.white,
          // color: DefaultPalette.white,
          display: 'flex',
          justifyContent: 'left',
      },
  };

  const stackItemCenterStyles: IStackItemStyles = {
      root: {
          alignItems: 'center',
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

  const promptTypeOptions = [
    {
      key: 'generic',
      text: 'generic'
    },
    {
      key: 'medical',
      text: 'medical'
    },
    {
      key: 'financial',
      text: 'financial'
    },
    {
      key: 'prospectus',
      text: 'prospectus'
    },
    {
      key: 'productdocmd',
      text: 'productdocmd'
    },
    {
      key: 'insurance',
      text: 'insurance'
    }
  ]

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

  const selection = useMemo(
    () =>
    new Selection({
        onSelectionChanged: () => {
        setSelectedItems(selection.getSelection());
    },
    selectionMode: SelectionMode.single,
    }),
  []);


  const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
    setSelectedChain(item);
  };

  const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
    setSelectedEmbeddingItem(item);
  };

  const onProspectusChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
    setSelectedProspectus(item);
    //getDocumentRuns(String(item?.key))
  };

  const onSummarizationTopicChanged = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
    if (item) {
        setSelectedSummaryTopicItem(
          item.selected ? [...selectedSummaryTopicItem, item.key as string] : selectedSummaryTopicItem.filter(key => key !== item.key),
        );
    }
  };

  const updatePrompt = (promptType: string) => {
    const genericPrompt = `"""You are an AI assistant tasked with answering questions and summarizing information from a long document. 
    Please generate a concise and comprehensive summary that includes details. 
    Ensure that the summary is easy to understand and provides an accurate representation. 
    Begin the summary with a brief introduction, followed by the main points.
    Generate the summary with minimum of 7 paragraphs and maximum of 10 paragraphs.
    Please remember to use clear language and maintain the integrity of the original information without missing any important details:
    {text}
    """`

    const medicalPrompt = `"""You are an AI assistant tasked with answering questions and summarizing information from medical records documents. 
    Your answer should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
    Please generate a concise and comprehensive information that includes details such as patient information, medical history, 
    allergies, chronic conditions, previous surgeries, prescribed medications, and upcoming appointments. 
    Ensure that it is easy to understand for healthcare professionals and provides an accurate representation of the patient's medical history 
    and current health status. 
    
    Begin with a brief introduction of the patient, followed by the main points of their medical records.
    Please remember to use clear language and maintain the integrity of the original information without missing any important details
    {text}
    """`

    const financialPrompt = `"""You are an AI assistant tasked with answering questions and summarizing information from 
    earning call transcripts, annual reports, SEC filings and financial statements like income statement, cashflow and 
    balance sheets. Additionally you may also be asked to answer questions about financial ratios and other financial metrics.
    The data that you are presented could be in table format or structure.
    Your answer should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
    Please generate a concise and comprehensive information that includes details such as reporting year and amount in millions.
    Ensure that it is easy to understand for business professionals and provides an accurate representation of the financial statement history. 
    
    Please remember to use clear language and maintain the integrity of the original information without missing any important details

    {text}
    """`

    const prospectusPrompt = `"""You are an AI assistant tasked with summarizing documents from large documents that contains information about Initial Public Offerings. 
    IPO document contains sections with information about the company, its business, strategies, risk, management structure, financial, and other information.
    Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
    Please generate a concise and comprehensive summary that includes details. 
    Ensure that the summary is easy to understand and provides an accurate representation. 
    Begin the summary with a brief introduction, followed by the main points.
    Generate the summary with minimum of 7 paragraphs and maximum of 10 paragraphs.
    Please remember to use clear language and maintain the integrity of the original information without missing any important details:
    {text}

    """`

    const productDocMdPrompt = `"""You are an AI assistant tasked with answering questions and summarizing information for 
        product or service from documentations and knowledge base.
        Your answer should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive information that includes details about the product or service.
        Please remember to use clear language and maintain the integrity of the original information without missing any important details
        QUESTION: {question}
        =========
        {summaries}
        =========

        """`

    if (promptType == "generic") {
        setPromptTemplate(genericPrompt)
    }
    else if (promptType == "medical") {
        setPromptTemplate(medicalPrompt)
    } else if (promptType == "financial") {
        setPromptTemplate(financialPrompt)
    } else if (promptType == "prospectus") {
        setPromptTemplate(prospectusPrompt)
    } else if (promptType == "productdocmd") {
        setPromptTemplate(productDocMdPrompt)
    } else if (promptType == "custom") {
        setPromptTemplate("")
    }
  }

  const refreshBlob = async () => {
    const files = []
    const indexType = []

    //const blobs = containerClient.listBlobsFlat(listOptions)
    const blobs = await refreshIndex()
    for (const blob of blobs.values) {
      if (blob.embedded == "true" && blob.singleFile == true)
      {
        files.push({
            text: blob.indexName,
            key: blob.namespace
        })
        indexType.push({
                key:blob.namespace,
                iType:blob.indexType,
                summary:blob.summary,
                qa:blob.qa == null ? '' : blob.qa,
                chunkSize:blob.chunkSize,
                chunkOverlap:blob.chunkOverlap,
                promptType:blob.promptType,
                singleFile:blob.singleFile,
                fileName:blob.name
        })
      }
    }
    var uniqFiles = files.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)
    setOptions(uniqFiles)
    setSelectedItem(uniqFiles[0])

    const defaultKey = uniqFiles[0].key
   
    var uniqIndexType = indexType.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)

    for (const item of uniqIndexType) {
        if (item.key == defaultKey) {
            setSelectedIndex(item.iType)
            setSelectedPromptTypeItem(promptTypeOptions.find(x => x.key === item.promptType))
            setSelectedDocument(item.fileName)
            setSelectedChunkSize(item.chunkSize)
            updatePrompt(item.promptType)

            if (Number(item.chunkSize) > 4000) {
                setSelectedDeploymentType(deploymentTypeOptions[1])
            }
            else {
                setSelectedDeploymentType(deploymentTypeOptions[0])
            }
        }
    }
    setIndexMapping(uniqIndexType)
  }

  const onDeploymentTypeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
    setSelectedDeploymentType(item);
  };

  const processedSummary = async () => {
    try {

        const request: AskRequest = {
            question : '',
            approach: Approaches.ReadDecomposeAsk,
            overrides: {
                promptTemplate: promptTemplate,
                fileName: String(selectedDocument),
                topics: selectedSummaryTopicItem.length === 0 ? undefined : selectedSummaryTopicItem,
                embeddingModelType: String(selectedEmbeddingItem?.key),
                chainType: String(selectedChain?.key),
                temperature: 0.3,
                tokenLength: 1500,
                top: 3,
                deploymentType: String(selectedDeploymentType?.key),
            }
        };
        setIsLoading(true);
        await processSummary(String(selectedItem?.key), String(selectedIndex), "true", request)
        .then(async (response: { answer: any; }) => {
                const answer = JSON.parse(JSON.stringify(response.answer));
                  const tQuestions = []
                  for (let i = 0; i < answer.length; i++) {
                      tQuestions.push({
                          "question": answer[i]['topic'],
                          "answer": answer[i]['summary'],
                      });
                      setSummaryQuestions(tQuestions);
                  }
            }
        )
        setIsLoading(false);
      } catch (e) {
        setError(e);
        setIsLoading(false);
    } finally {
        setIsLoading(false);
    }
  }

  const processSummarization = async () => {
    try {

        if (customTopic != '') {
          const addTopic = customTopic.split(",")
          if (addTopic.length > 0) {
            for (let i = 0; i < addTopic.length; i++) {
                if (addTopic[i] != '') {
                  selectedSummaryTopicItem.push(addTopic[i])
                }
            }
          } else {
            selectedSummaryTopicItem.push(customTopic)
          }
        }
        const uniqTopics = [...new Set(selectedSummaryTopicItem)]
        setSelectedSummaryTopicItem(uniqTopics)

        const request: AskRequest = {
            question : '',
            approach: Approaches.ReadDecomposeAsk,
            overrides: {
                promptTemplate: promptTemplate,
                fileName: String(selectedDocument),
                topics: uniqTopics.length === 0 ? undefined : uniqTopics,
                embeddingModelType: String(selectedEmbeddingItem?.key),
                chainType: String(selectedChain?.key),
                temperature: 0.3,
                tokenLength: 1500,
                top: 3,
                deploymentType: String(selectedDeploymentType?.key),
            }
        };
        setIsLoading(true);
        await processSummary(String(selectedItem?.key), String(selectedIndex), "false", request)
        .then(async (response: { answer: any; }) => {
                const answer = JSON.parse(JSON.stringify(response.answer));
                  const tQuestions = []
                  for (let i = 0; i < answer.length; i++) {
                      tQuestions.push({
                          "question": answer[i]['topic'],
                          "answer": answer[i]['summary'],
                      });
                      setSummaryQuestions(tQuestions);
                  }
            }
        )
        setIsLoading(false);
      } catch (e) {
        setError(e);
        setIsLoading(false);
    } finally {
        setIsLoading(false);
    }
  }

  const onCustomTopicChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
    setCustomTopic(newValue || "");
  };

  const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
    setSelectedItem(item);
    const defaultKey = item?.key
    indexMapping?.findIndex((item) => {
        if (item.key == defaultKey) {
            setSelectedIndex(item.iType)
            setSelectedDocument(item.fileName)
            setSummaryQuestions([])
            setSelectedChunkSize(item.chunkSize)
            // setSelectedChunkOverlap(item.chunkOverlap)
            //setSelectedPromptType(item.promptType)
            setSelectedPromptTypeItem(promptTypeOptions.find(x => x.key === item.promptType))
            updatePrompt(item.promptType)

            if (Number(item.chunkSize) > 4000) {
                setSelectedDeploymentType(deploymentTypeOptions[1])
            }
            else {
                setSelectedDeploymentType(deploymentTypeOptions[0])
            }
        }
    })
  };

  const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
    setPromptTemplate(newValue || "");
  };

  useEffect(() => {
    const defaultSummaryPrompt = `"""You are an AI assistant tasked with summarizing documents from large documents that contains information about Initial Public Offerings. 
        IPO document contains sections with information about the company, its business, strategies, risk, management structure, financial, and other information.
        Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive summary that includes details. 
        Ensure that the summary is easy to understand and provides an accurate representation. 
        Begin the summary with a brief introduction, followed by the main points.
        Generate the summary with minimum of 7 paragraphs and maximum of 10 paragraphs.
        Please remember to use clear language and maintain the integrity of the original information without missing any important details:
        {text}

        """`
    
    setPromptTemplate(defaultSummaryPrompt)
    setSelectedEmbeddingItem(embeddingOptions[0])
    setSelectedChain(chainTypeOptions[1])
    setSelectedSummaryTopicItem(['Strengths', 'Growth Strategy'])
    refreshBlob()
    setSelectedEmbeddingItem(embeddingOptions[0])
    setSummaryQuestions([])
    setSelectedDeploymentType(deploymentTypeOptions[0])

  }, [])

  return (
      <div className={styles.chatAnalysisPanel}>
          <Stack enableScopedSelectors tokens={outerStackTokens}>
            <Stack enableScopedSelectors  tokens={innerStackTokens}>
              <Stack.Item grow styles={stackItemStyles}>
                <DefaultButton onClick={refreshBlob}>Refresh Docs</DefaultButton>
                &nbsp;
                <Dropdown
                    selectedKey={selectedItem ? selectedItem.key : undefined}
                    // eslint-disable-next-line react/jsx-no-bind
                    onChange={onChange}
                    placeholder="Select an PDF"
                    options={options}
                    styles={dropdownStyles}
                />
                &nbsp;
                {/* <Label className={styles.commandsContainer}>Index Type : {selectedIndex}</Label>
                <Label className={styles.commandsContainer}>Chunk Size : {selectedChunkSize} / Chunk Overlap : {selectedChunkOverlap}</Label> */}
                &nbsp;
                <Label>Embedding Model</Label>
                &nbsp;
                <Dropdown
                    selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                    onChange={onEmbeddingChange}
                    placeholder="Select an Embedding Model"
                    options={embeddingOptions}
                    disabled={false}
                    styles={dropdownShortStyles}
                />
                &nbsp;
                <Label>Deployment Type</Label>
                &nbsp;
                <Dropdown
                        selectedKey={selectedDeploymentType ? selectedDeploymentType.key : undefined}
                        onChange={onDeploymentTypeChange}
                        //defaultSelectedKey="azureopenai"
                        placeholder="Select an Deployment Type"
                        options={deploymentTypeOptions}
                        disabled={((selectedEmbeddingItem?.key == "openai" ? true : false) || (Number(selectedChunkSize) > 4000 ? true : false))}
                        styles={dropdownShortStyles}
                />
                &nbsp;
                <Label>Chain Type</Label>
                &nbsp;
                <Dropdown 
                    onChange={onChainChange}
                    selectedKey={selectedChain ? selectedChain.key : 'stuff'}
                    options={chainTypeOptions}
                    disabled={false}
                    styles={dropdownShortStyles}
                />
              </Stack.Item>
            </Stack>
          </Stack>
          <Stack enableScopedSelectors styles={stackItemCenterStyles} tokens={innerStackTokens}>
            <Stack.Item grow={2} styles={stackItemCenterStyles}>
                {/* <PrimaryButton text="RefreshDocs" onClick={() => processSummarization()} disabled={true} />
                <Label>Select Document:</Label>&nbsp;
                <Dropdown
                    selectedKey={selectedProspectus ? selectedProspectus.key : undefined}
                    // eslint-disable-next-line react/jsx-no-bind
                    onChange={onProspectusChange}
                    placeholder="Select an Prospectus"
                    options={prospectus}
                    styles={dropdownStyles}
                />
                &nbsp; */}
                <Label>Summarization Topics</Label>
                &nbsp;
                <Dropdown
                    selectedKeys={selectedSummaryTopicItem}
                    onChange={onSummarizationTopicChanged}
                    //defaultSelectedKeys={['RecursiveCharacterTextSplitter']}
                    placeholder="Select Topic"
                    options={summaryTopicOptions}
                    disabled={false}
                    styles={dropdownStyles}
                    multiSelect
                />
                &nbsp;
                <Label>Custom Topics</Label>
                &nbsp;
                <TextField value={customTopic} onChange={onCustomTopicChange} />
                &nbsp;
                <PrimaryButton text="Summarize" onClick={() => processSummarization()} />
                &nbsp;
                <PrimaryButton text="Show Processed Summary" onClick={() => processedSummary()} />
                <br/>
            </Stack.Item>
            <Stack.Item grow={2} styles={stackItemCenterStyles}>
                <TextField label="Prompt" multiline rows={10} value={promptTemplate} 
                  style={{ width: 800, height: 300 }}
                  onChange={onPromptTemplateChange} />
            </Stack.Item>
            <br/>
            {isLoading ? (
                <Stack.Item grow={2} styles={stackItemStyles}>
                    <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                </Stack.Item>
                ) : (
                <Stack.Item grow={2} styles={stackItemCenterStyles}>
                    <DetailsList
                        compact={false}
                        items={summaryQuestions || []}
                        columns={summaryColumns}
                        selectionMode={SelectionMode.none}
                        getKey={(item: any) => item.key}
                        selectionPreservedOnEmptyClick={true}
                        layoutMode={DetailsListLayoutMode.justified}
                        ariaLabelForSelectionColumn="Toggle selection"
                        checkButtonAriaLabel="select row"
                        />
                </Stack.Item>
            )}
        </Stack>
      </div>
    );
};

export default Summary;
