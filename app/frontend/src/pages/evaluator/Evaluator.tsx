import { useState, useEffect } from "react";

import { Dropdown, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';
import { DefaultButton, Pivot, Spinner, PivotItem, Link } from '@fluentui/react';

import styles from "./Evaluator.module.css";
import { Label } from '@fluentui/react/lib/Label';
import { Card, CardFooter} from "@fluentui/react-components";
import { getDocumentList, getAllDocumentRuns, getEvaluationQaDataSet, getEvaluationResults, uploadEvaluatorFile, verifyPassword,
    runEvaluation } from "../../api";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ChatSession } from "../../api/models";
import { DetailsList, DetailsListLayoutMode, SelectionMode, Selection} from '@fluentui/react/lib/DetailsList';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';
import { Stack, IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { PrimaryButton } from "@fluentui/react";
import { TextField } from '@fluentui/react/lib/TextField';
import { useDropzone } from 'react-dropzone'
import { BarcodeScanner24Filled } from "@fluentui/react-icons";

const Evaluator = () => {
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 400 } };
    const dropdownShortStyles: Partial<IDropdownStyles> = { dropdown: { width: 150 } };

    const [files, setFiles] = useState<any>([])
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);

    const [documents, setDocuments] = useState<any>([])
    const [selectedDocument, setSelectedDocument] = useState<IDropdownOption>();
    const [documentRuns, setDocumentRuns] = useState<any>([])
    const [selectedRunId, setSelectdRunId] = useState<IDropdownOption>();
    const [evaluationQaDataSet, setEvaluationQaDataSet] = useState<any>([])
    const [evaluationResults, setEvaluationResults] = useState<any>();
    const [uploadText, setUploadText] = useState('');
    const [uploadPassword, setUploadPassword] = useState('');
    const [missingUploadPassword, setMissingUploadPassword] = useState(false)
    const [uploadError, setUploadError] = useState(false)
    const [selectedTextSplitterItem, setSelectedTextSplitterItem] = useState<string[]>([]);
    const [selectedChunkSizeItem, setSelectedChunkSizeItem] = useState<string[]>([]);
    const [selectedChunkOverlapItem, setSelectedChunkOverlapItem] = useState<string[]>([]);
    const [selectedTotalQuestionItem, setSelectedTotalQuestionItem] = useState<IDropdownOption>();
    const [selectedModelItem, setSelectedModelItem] = useState<IDropdownOption>();
    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const [selectedPromptStyleItem, setSelectedPromptStyleItem] = useState<IDropdownOption>();
    const [statusLink, setStatusLink] = useState<string>('');
    
    const promptStyleOptions = [
    {
        key: 'Descriptive',
        text: 'Descriptive'
    },
    {
        key: 'Fast',
        text: 'Fast'
    },
    {
        key: 'Bias',
        text: 'Bias'
    }
    ]    

    const textSplitterOptions = [
        {
          key: 'RecursiveCharacterTextSplitter',
          text: 'Recursive Character Text Splitter'
        },
        {
          key: 'TikToken',
          text: 'Tik Token'
        },
        {
          key: 'NLTKTextSplitter',
          text: 'NLTK Text Splitter'
        },
        {
          key: 'FormRecognizer',
          text: 'Form Recognizer'
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
    ]

    const modelOptions = [
    {
        key: 'GPT3.5',
        text: 'GPT3.5'
    },
    {
        key: 'GPT4',
        text: 'GPT4'
    }
    ]

    const totalQuestionsOptions = [
    {
        key: '5',
        text: '5'
    },
    {
        key: '10',
        text: '10'
    },
    {
        key: '15',
        text: '15'
    }
    ]

    const chunkSizeOptions = [
        {
          key: '500',
          text: '500'
        },
        {
          key: '1000',
          text: '1000'
        },
        {
          key: '1500',
          text: '1500'
        },
        {
          key: '2000',
          text: '2000'
        }
    ]

    const chunkOverlapOptions = [
        {
          key: '0',
          text: '0'
        },
        {
          key: '50',
          text: '50'
        },
        {
          key: '100',
          text: '100'
        },
        {
          key: '150',
          text: '150'
        }
    ]

    const evaluationQaDataSetColumns = [
        {
          key: 'question',
          name: 'Question',
          fieldName: 'question',
          minWidth: 150, maxWidth: 350, isResizable: false, isMultiline: true
        },
        {
          key: 'answer',
          name: 'Answer',
          fieldName: 'answer',
          minWidth: 500, maxWidth: 1000, isResizable: false, isMultiline: true
        }
    ]

    const evaluationResultsColumns = [
        {
          key: 'question',
          name: 'Question',
          fieldName: 'Question',
          minWidth: 100, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
          key: 'answer',
          name: 'Expected Answer',
          fieldName: 'Answer',
          minWidth: 100, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
            key: 'predictedAnswer',
            name: 'Predicted Answer',
            fieldName: 'Predicted Answer',
            minWidth: 100, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
            key: 'ajustification',
            name: 'Answer Justification',
            fieldName: 'Answer Justification',
            minWidth: 100, maxWidth: 250, isResizable: false, isMultiline: true
        },
        {
            key: 'rjustification',
            name: 'Retrieval Justification',
            fieldName: 'Retrieval Justification',
            minWidth: 100, maxWidth: 250, isResizable: false, isMultiline: true
        },
        {
            key: 'splitMethod',
            name: 'Split Method',
            fieldName: 'Split Method',
            minWidth: 150, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
            key: 'chunkSize',
            name: 'Chunk Size',
            fieldName: 'Chunk Size',
            minWidth: 50, maxWidth: 100, isResizable: false
        },
        {
            key: 'overlap',
            name: 'Overlap',
            fieldName: 'Overlap',
            minWidth: 50, maxWidth: 100, isResizable: false
        },
        {
            key: 'latency',
            name: 'Latency',
            fieldName: 'Latency',
            minWidth: 50, maxWidth: 100, isResizable: false
        }
    ]

    const { getRootProps, getInputProps } = useDropzone({
        multiple: false,
        maxSize: 100000000,
        accept: {
          'application/pdf': ['.pdf'],
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

    const stackStyles: IStackStyles = {
        root: {
          // background: DefaultPalette.white,
          height: 450,
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
  
    // Tokens definition
    const outerStackTokens: IStackTokens = { childrenGap: 5 };
    const innerStackTokens: IStackTokens = {
        childrenGap: 5,
        padding: 10,
    };
    
    const getDocuments = async () => {
        try {
            await getDocumentList()
            .then(async (response:any) => {
                const documentLists = []
                for (const document of response.values)
                {
                    documentLists.push({
                            key:document.documentId, 
                            text:document.documentName,
                            sourceFile:document.sourceFile,
                        });
                }
                setDocuments(documentLists);
                setSelectedDocument(documentLists[0])
                getDocumentRuns(documentLists[0].key)
            }
            )
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    }

    const getDocumentRuns = async (documentId:string) => {
        try {
            await getAllDocumentRuns(documentId)
            .then(async (response:any) => {
                const runLists = []
                for (const run of response.values)
                {
                    runLists.push({
                            key:run.runId, 
                            text:run.runId,
                        });
                }
                var uniqRuns = runLists.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)
                setDocumentRuns(uniqRuns)         
                setSelectdRunId(uniqRuns[0])
            })
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    }

    const onRunEvaluation = async () => {
        try {
            await getEvaluationQaDataSet(String(selectedDocument?.key))
            .then(async (qaResponse:any) => {
                const evaluationQaLists = []
                for (const evaluation of qaResponse.values)
                {
                    evaluationQaLists.push({
                            key:evaluation.questionId, 
                            question:evaluation.question,
                            answer:evaluation.answer,
                        });
                }
                setEvaluationQaDataSet(evaluationQaLists);
                await getEvaluationResults(String(selectedDocument?.key), String(selectedRunId?.key))
                .then(async (resultResponse:any) => {
                    const evaluationResult = []
                    for (const evaluation of resultResponse.values)
                    {
                        evaluationResult.push({
                            "Question": evaluation['question'],
                            "Answer": evaluation['answer'],
                            "Predicted Answer": evaluation['predictedAnswer'],
                            "Retriever Type": evaluation['retrieverType'],
                            "Prompt Style": evaluation['promptStyle'],
                            "Split Method": evaluation['splitMethod'],
                            "Chunk Size": evaluation['chunkSize'],
                            "Overlap": evaluation['overlap'],
                            //"Answer Score": JSON.parse(evaluation['answerScore'])['score'],
                            "Answer Justification": JSON.parse(evaluation['answerScore'])['justification'],
                            //"Retrieval Score": JSON.parse(evaluation['retrievalScore'])['score'],
                            "Retrieval Justification": JSON.parse(evaluation['retrievalScore'])['justification'],
                            "Latency": evaluation['latency'],
                            });
                    }
                    setEvaluationResults(evaluationResult);
                })
            })
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    }

    useEffect(() => {
        getDocuments();
        setSelectedTextSplitterItem(['RecursiveCharacterTextSplitter'])
        setSelectedChunkOverlapItem(['0'])
        setSelectedChunkSizeItem(['500'])
        setSelectedEmbeddingItem(embeddingOptions[0])
        setSelectedModelItem(modelOptions[0])
        setSelectedTotalQuestionItem(totalQuestionsOptions[0])
        setSelectedPromptStyleItem(promptStyleOptions[0])
    }, [])

    const handleRemoveFile = (file: File ) => {
        const uploadedFiles = files
        //const filtered = uploadedFiles.filter(i => i.name !== file.name)
        const filtered = uploadedFiles.filter((i: { name: string; }) => i.name !== file.name)
        setFiles([...filtered])
    }

    const handleRemoveAllFiles = () => {
        setFiles([])
    }

    const onTextSplitterChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item) {
            setSelectedTextSplitterItem(
              item.selected ? [...selectedTextSplitterItem, item.key as string] : selectedTextSplitterItem.filter(key => key !== item.key),
            );
        }
    };

    const onChunkSizeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item) {
            setSelectedChunkSizeItem(
              item.selected ? [...selectedChunkSizeItem, item.key as string] : selectedChunkSizeItem.filter(key => key !== item.key),
            );
        }
    };

    const onChunkOverlapChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item) {
            setSelectedChunkOverlapItem(
              item.selected ? [...selectedChunkOverlapItem, item.key as string] : selectedChunkOverlapItem.filter(key => key !== item.key),
            );
        }
    };

    const onTotalQuestionChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedTotalQuestionItem(item);
    };

    const onModelChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedModelItem(item);
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItem(item);
    };

    const onPromptStyleChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedPromptStyleItem(item);
    };

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
          <DefaultButton onClick={() => handleRemoveFile(file)} disabled={isLoading ? true : false}>Remove File</DefaultButton>
        </div>
    ))

    const handleUploadFiles = async () => {
        if (uploadPassword == '') {
          setMissingUploadPassword(true)
          return
        }
  
        setIsLoading(true)
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
      
                await uploadEvaluatorFile(formData)
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
            setUploadText("File uploaded successfully.  Now Running the Evaluation.")
 
            await runEvaluation(selectedChunkOverlapItem, selectedChunkSizeItem,
                selectedTextSplitterItem, String(selectedTotalQuestionItem?.key),
                String(selectedModelItem?.key), String(selectedEmbeddingItem?.key), String(selectedPromptStyleItem?.key),
                files[0].name, "SimilaritySearch")
                .then((response:string) => {
                    setStatusLink(response)
                    setUploadText("Click on the status link below to view the status of your evaluation.")
                    setFiles([])
                    setIsLoading(false)
                })
                .catch((error : string) => {
                    setUploadText(error)
                    setFiles([])
                    setIsLoading(false)
            })
          }
          else {
            setUploadText(verifyResponse)
          }
        })
        .catch((error : string) => {
          setUploadText(error)
          setFiles([])
          setIsLoading(false)
        })
        setIsLoading(false)
    }

    const onDocumentNameChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedDocument(item);
        getDocumentRuns(String(item?.key))
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

    const onToggleTab = (tab: AnalysisPanelTabs, index: number) => {
        if (activeAnalysisPanelTab === tab && selectedAnswer === index) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }

        setSelectedAnswer(index);
    };

    return (
        <div className={styles.root}>
            <div className={styles.container}>
                <Pivot aria-label="Chat">
                    <PivotItem
                        headerText="Run Evaluation"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                        <Stack enableScopedSelectors tokens={outerStackTokens}>
                            <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <div className={styles.example}>
                                        <p><b>Run Evaluation</b> : This feature focuses on performing the LLM based evaluation on your document.
                                        It auto-generates the test dataset (with Question and Answers) and perform the grading on that document using different parameters
                                        and generates the evaluation results.   To execute the evaluation, you need to 1) select (one or multiple) Chunking method that are supported here,
                                        2) one ore multiple chunk size (500, 1000, 1500, 2000), 3) one ore multiple Chunk Overlap (0, 50, 100, 150), 4) model you want to use to run evaluation against (GPT3.5 or 4),
                                        5) total # of questions you want to auto-generate and run the evaluation against and 6) prompty style</p>
                                        <p>
                                            Upon invoking the process, Azure Durable Function will be invoked and it will run the evaluation against the document and generate the results.
                                            Following are the steps that are performed by the Durable Function:
                                            <ul>
                                                <li>Using Langchain generate the test dataset (with Question and Answers) and store it in Cognitive Search Index</li>
                                                <li>For each selected Chunking method, Chunk Size and Chunk Overlap, it will generate the evaluation results and store it in Cognitive Search Index</li>
                                                <li>For each selected Chunking method, Chunk Size and Chunk Overlap, it will grade the answer by evaluate the relevance of retrieved document and similarity of generated answer</li>
                                                <li>It will generate the evaluation results and store it in Cognitive Search Index</li>
                                            </ul>
                                        </p>
                                        <p>
                                            Because it is asynchronous process, upon uploading the document, you can check the status of the evaluation by clicking on the "Check Status" button.
                                            Completed Evaluation Run can be viewed in the "View Evaluation" tab
                                        </p>
                                    </div>
                                </Stack.Item>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <Label>Chunk Document using :</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKeys={selectedTextSplitterItem}
                                        onChange={onTextSplitterChange}
                                        //defaultSelectedKeys={['RecursiveCharacterTextSplitter']}
                                        placeholder="Select text splitter"
                                        options={textSplitterOptions}
                                        disabled={false}
                                        styles={dropdownStyles}
                                        multiSelect
                                    />
                                    &nbsp;
                                    <Label>Chunk Sizes :</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKeys={selectedChunkSizeItem}
                                        onChange={onChunkSizeChange}
                                        //defaultSelectedKeys={['500']}
                                        placeholder="Select Chunk Size"
                                        options={chunkSizeOptions}
                                        disabled={false}
                                        styles={dropdownShortStyles}
                                        multiSelect
                                    />
                                    &nbsp;
                                    <Label>Chunk Overlap :</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKeys={selectedChunkOverlapItem}
                                        onChange={onChunkOverlapChange}
                                        //defaultSelectedKeys={['0']}
                                        placeholder="Select Overlap"
                                        options={chunkOverlapOptions}
                                        disabled={false}
                                        styles={dropdownShortStyles}
                                        multiSelect={true}
                                    />
                                    &nbsp;
                                    <Label>Model :</Label>&nbsp;
                                    <Dropdown
                                        selectedKey={selectedModelItem?.key}
                                        onChange={onModelChange}
                                        defaultSelectedKey="GPT3.5"
                                        placeholder="Select Model"
                                        options={modelOptions}
                                        disabled={false}
                                        styles={dropdownShortStyles}
                                        multiSelect={false}
                                    />
                                </Stack.Item>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <Label>Total Questions :</Label>&nbsp;
                                    <Dropdown
                                        selectedKey={selectedTotalQuestionItem?.key}
                                        onChange={onTotalQuestionChange}
                                        defaultSelectedKey="5"
                                        placeholder="Select Total Questions"
                                        options={totalQuestionsOptions}
                                        disabled={false}
                                        styles={dropdownShortStyles}
                                        multiSelect={false}
                                    />
                                    &nbsp;
                                    <Label>Embedding Model :</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                                        onChange={onEmbeddingChange}
                                        defaultSelectedKey="azureopenai"
                                        placeholder="Select an Embedding Model"
                                        options={embeddingOptions}
                                        disabled={false}
                                        styles={dropdownShortStyles}
                                    />
                                    &nbsp;
                                    <Label>Prompt Style :</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKey={selectedPromptStyleItem ? selectedPromptStyleItem.key : undefined}
                                        onChange={onPromptStyleChange}
                                        defaultSelectedKey="Descriptive"
                                        placeholder="Select an Prompt Style"
                                        options={promptStyleOptions}
                                        disabled={false}
                                        styles={dropdownShortStyles}
                                    />
                                </Stack.Item>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <Label>Evaluator Password:</Label>&nbsp;
                                    <TextField onChange={onUploadPassword}
                                        errorMessage={!missingUploadPassword ? '' : "Note - Upload Password is required for Evaluation Functionality"}/>
                                </Stack.Item>
                            </Stack>
                            <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                                <Stack.Item grow={2} styles={stackItemStyles}>
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
                                                    <DefaultButton onClick={handleRemoveAllFiles} disabled={isLoading ? true : false}>Remove All</DefaultButton>
                                                    <DefaultButton onClick={handleUploadFiles} disabled={isLoading ? true : false}>
                                                        <span>Process File</span>
                                                    </DefaultButton>
                                                </CardFooter>
                                            </Card>
                                        ) : null}
                                        <br/>
                                        {isLoading ? <div><span>Please wait, Uploading and Processing your file</span><Spinner/></div> : null}
                                        <hr />
                                        <h2 className={styles.chatEmptyStateSubtitle}>
                                            <TextField disabled={true} label={uploadError ? '' : uploadText} errorMessage={!uploadError ? '' : uploadText} />
                                        </h2>
                                        <h3 className={styles.chatEmptyStateSubtitle}>
                                            <Link disabled={statusLink.length==0} href={statusLink} underline> Check Status </Link>
                                        </h3>
                                    </div>
                                </Stack.Item>
                            </Stack>
                        </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="View Evaluation"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                        <Stack enableScopedSelectors tokens={outerStackTokens}>
                            <Stack enableScopedSelectors styles={stackStyles} tokens={innerStackTokens}>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <div className={styles.example}>
                                        <p ><b>Summary</b> : This tab shows the performance evaluated on the documents that you uploaded to 
                                        run through question-answering LLM chains. The aim is to evaluate the performance of various question-answering LLM chain configurations 
                                        against the test set that is automatically generated as part of the evaluation. </p>
                                        <p ><b>Instructions</b> : Select a document and a runId to view the evaluation results. </p>
                                    </div>
                                </Stack.Item>
                                <br/>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <PrimaryButton text="Refresh Documents" onClick={getDocuments} />
                                    &nbsp;
                                    <Label>Document Name</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKey={selectedDocument ? selectedDocument.key : undefined}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        onChange={onDocumentNameChange}
                                        placeholder="Select an Document"
                                        options={documents}
                                        styles={dropdownStyles}
                                    />
                                    &nbsp;
                                    <Label>Document Run</Label>
                                    &nbsp;
                                    <Dropdown
                                        selectedKey={selectedRunId ? selectedRunId.key : undefined}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        //onChange={onDocumentRunChange}
                                        placeholder="Select an Run"
                                        options={documentRuns}
                                        styles={dropdownStyles}
                                    />
                                    &nbsp;
                                    <PrimaryButton text="View Results" onClick={onRunEvaluation} />
                                </Stack.Item>
                                <br/>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <div className={styles.example}>
                                        <p><b>Test Dataset</b> : Following table shows the test dataset that was generated for the document
                                        you selected.  It uses QAGenerationChain capabilities from Langchain.  It shows the question and the ground truth (expected) answer based
                                        on the document you uploaded.</p>
                                    </div>
                                </Stack.Item>
                                <Stack.Item grow>
                                    <div>
                                        <DetailsList
                                            compact={true}
                                            items={evaluationQaDataSet || []}
                                            columns={evaluationQaDataSetColumns}
                                            selectionMode={SelectionMode.none}
                                            getKey={(item: any) => item.key}
                                            selectionPreservedOnEmptyClick={true}
                                            layoutMode={DetailsListLayoutMode.justified}
                                            ariaLabelForSelectionColumn="Toggle selection"
                                            checkButtonAriaLabel="select row"
                                        />
                                    </div>
                                </Stack.Item>
                                <br/>
                                <Stack.Item grow={2} styles={stackItemStyles}>
                                    <div className={styles.example}>
                                        <p><b>Experiment Results</b> : This table shows the each question-answer pair from the test dataset along 
                                        with the model's (that you selected during run - GPT3.5 or GPT4) to predict the answer to the question. 
                                        Along with the predicted answer it also shows two things: (1) the relevance of the retrieved documents relative to the question and 
                                        (2) the similarity of the LLM generated answer relative to ground truth answer. The prompts for both can be selected as a part of the execution run
                                        in the drop-down list "Grading prompt style". The "Fast" prompt will only have the LLM grader output the score. 
                                        The other prompts will also produce an explanation.</p>
                                    </div>
                                </Stack.Item>
                                <Stack.Item grow>
                                    <div>
                                        <DetailsList
                                            compact={true}
                                            items={evaluationResults || []}
                                            columns={evaluationResultsColumns}
                                            selectionMode={SelectionMode.none}
                                            getKey={(item: any) => item.key}
                                            selectionPreservedOnEmptyClick={true}
                                            layoutMode={DetailsListLayoutMode.justified}
                                            ariaLabelForSelectionColumn="Toggle selection"
                                            checkButtonAriaLabel="select row"
                                            />
                                    </div>
                                </Stack.Item>
                            </Stack>
                            </Stack>
                    </PivotItem>
              </Pivot>
            </div>
        </div>
    );
};

export default Evaluator;
