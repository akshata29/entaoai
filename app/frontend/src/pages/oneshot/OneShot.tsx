import { useRef, useState, useEffect } from "react";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, Stack, IPivotItemProps, getFadedOverflowStyle} from "@fluentui/react";

import styles from "./OneShot.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { askApi, askAgentApi, askTaskAgentApi, Approaches, AskResponse, AskRequest, refreshIndex, getSpeechApi, summaryAndQa, refreshQuestions } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { BlobServiceClient } from "@azure/storage-blob";
import { Label } from '@fluentui/react/lib/Label';
import { ExampleList, ExampleModel } from "../../components/Example";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";
import { QuestionListButton } from "../../components/QuestionListButton/QuestionListButton";
import { ClearChatButton } from "../../components/ClearChatButton";
import { Pivot, PivotItem } from '@fluentui/react';
import { IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { DefaultPalette } from '@fluentui/react/lib/Styling';
import { DetailsList, DetailsListLayoutMode, SelectionMode, ConstrainMode } from '@fluentui/react/lib/DetailsList';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';

var audio = new Audio();

const OneShot = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [isQuestionPanelOpen, setIsQuestionPanelOpen] = useState(false);
    const [approach, setApproach] = useState<Approaches>(Approaches.RetrieveThenRead);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplatePrefix, setPromptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix, setPromptTemplateSuffix] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [temperature, setTemperature] = useState<number>(0);
    const [tokenLength, setTokenLength] = useState<number>(1000);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(true);
    const [useAutoSpeakAnswers, setUseAutoSpeakAnswers] = useState<boolean>(false);

    const [lastHeader, setLastHeader] = useState<{ props: IPivotItemProps } | undefined>(undefined);

    const [options, setOptions] = useState<any>([])
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };

    const lastQuestionRef = useRef<string>("");
    const lastAgentQuestionRef = useRef<string>("");
    const lastTaskAgentQuestionRef = useRef<string>("");

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    //const [answer, setAnswer] = useState<AskResponse>();
    const [answer, setAnswer] = useState<[AskResponse, string | null]>();

    const [errorAgent, setAgentError] = useState<unknown>();
    const [errorTaskAgent, setTaskAgentError] = useState<unknown>();
    //const [answerAgent, setAgentAnswer] = useState<AskResponse>();
    const [answerAgent, setAgentAnswer] = useState<[AskResponse, string | null]>();
    const [answerTaskAgent, setTaskAgentAnswer] = useState<[AskResponse, string | null]>();


    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();

    //const [selectedIndex, setSelectedIndex] = useState<IDropdownOption>();
    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string;  summary:string; qa:string;}[]>();
    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [summary, setSummary] = useState<string>();
    const [agentSummary, setAgentSummary] = useState<string>();
    const [taskAgentSummary, setTaskAgentSummary] = useState<string>();
    const [qa, setQa] = useState<string>('');
    const [exampleLoading, setExampleLoading] = useState(false)
    const [chainTypeOptions, setChainTypeOptions] = useState<any>([])

    const [filteredOptions, setFilteredOptions] = useState<any>([])
    const [selectedindexTypeItem, setSelectedindexTypeItem] = useState<IDropdownOption>();
    const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
    const [selectedText, setSelectedText] = useState<string[]>([]);
    const [selectedIndexes, setSelectedIndexes] = useState<{ indexNs: string; indexName: any; returnDirect: string; }[]>([]);
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

    const [filteredTaskAgentOptions, setFilteredTaskAgentOptions] = useState<any>([])
    const [selectedTaskAgentKeys, setSelectedTaskAgentKeys] = useState<string[]>([]);
    const [selectedTaskAgentText, setSelectedTaskAgentText] = useState<string[]>([]);
    const [selectedTaskAgentIndexes, setSelectedTaskAgentIndexes] = useState<{ indexNs: string; indexName: any; returnDirect: string; }[]>([]);
    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const [questionList, setQuestionList] = useState<any[]>();

    const classNames = mergeStyleSets({
        header: {
          margin: 0,
        },
        row: {
          flex: '0 0 auto',
        },
        focusZone: {
          height: '100%',
          overflowY: 'auto',
          overflowX: 'hidden',
        },
        selectionZone: {
          height: '100%',
          overflow: 'hidden',
        },
      });

    const focusZoneProps = {
        className: classNames.focusZone,
        'data-is-scrollable': 'true',
    } as React.HTMLAttributes<HTMLElement>;

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

    const indexTypeOptions = [
        {
          key: 'pinecone',
          text: 'Pinecone'
        },
        {
          key: 'redis',
          text: 'Redis Stack'
        }
        // {
        //   key: 'chroma',
        //   text: 'Chroma'
        // }
    ]

    const questionListColumn = [
        {
          key: 'question',
          name: 'Question',
          fieldName: 'question',
          minWidth: 100, maxWidth: 200, isResizable: true
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

     // Tokens definition
     const outerStackTokens: IStackTokens = { childrenGap: 5 };
     const innerStackTokens: IStackTokens = {
       childrenGap: 5,
       padding: 10,
    };

    const chainType = [
        { key: 'stuff', text: 'Stuff'},
        { key: 'map_rerank', text: 'Map ReRank' },
        { key: 'map_reduce', text: 'Map Reduce' },
        { key: 'refine', text: 'Refine'},
    ]

    const refreshFilteredBlob = async(selectedIndex : string) => {
        const files = []
        const indexType = []
    
        //const blobs = containerClient.listBlobsFlat(listOptions)
        const blobs = await refreshIndex()       
        for (const blob of blobs.values) {
          if (blob.embedded == "true" && blob.indexType == selectedIndex)
          {
            files.push({
                text: blob.indexName,
                key: blob.namespace
            })
            indexType.push({
                    key:blob.namespace,
                    iType:blob.indexType,
                    summary:blob.summary,
                    qa:blob.qa
            })
          }
        }
        var uniqFiles = files.filter((v,i,a)=>a.findIndex(v2=>(v2.key===v.key))===i)
        setFilteredOptions(uniqFiles)
        setFilteredTaskAgentOptions(uniqFiles)
    }

    const onIndexChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedindexTypeItem(item);
        refreshFilteredBlob(String(item?.key))
    };

    const onFilteredOptionChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item) {
            setSelectedKeys(
                item.selected ? [...selectedKeys, item.key as string] : selectedKeys.filter(key => key !== item.key),
            );
            setSelectedIndexes(
                item.selected ? [...selectedIndexes, {"indexNs":item.key as string, "indexName": item.text, "returnDirect": "False"}] : selectedIndexes.filter(key => key.indexNs !== item.key),
            );
            setSelectedText(
                item.selected ? [...selectedText, item.text as string] : selectedText.filter(key => key !== item.text),
            );
            setAgentSummary("This sample shows using Agents use an LLM to determine which actions to take and in what order." + 
            " An action can either be using a tool and observing its output, or returning to the user.  Agent will go against the" + 
            " set of the documents that you select here - " + (item.selected ? [...selectedText, item.text as string] : selectedText.filter(key => key !== item.text)))
        }
    };

    const onFilteredTaskAgentOptionChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item) {
            setSelectedTaskAgentKeys(
                item.selected ? [...selectedTaskAgentKeys, item.key as string] : selectedTaskAgentKeys.filter(key => key !== item.key),
            );
            setSelectedTaskAgentIndexes(
                item.selected ? [...selectedTaskAgentIndexes, {"indexNs":item.key as string, "indexName": item.text, "returnDirect": "False"}] : selectedTaskAgentIndexes.filter(key => key.indexNs !== item.key),
            );
            setSelectedTaskAgentText(
                item.selected ? [...selectedTaskAgentText, item.text as string] : selectedTaskAgentText.filter(key => key !== item.text),
            );
            setTaskAgentSummary("This sample demonstrates how to implement BabyAGI by Yohei Nakajima. BabyAGI is an AI agent that can generate and pretend to execute tasks based on a given objective." +
            " An action can either be using a tool and observing its output, or returning to the user.  " + 
            " It is example of an AI-powered task management system. The system uses OpenAI and creates, prioritize, and execute tasks. " + 
            " The main idea behind this system is that it creates tasks based on the result of previous tasks and a predefined objective. " +
            " The script then uses OpenAI's natural language processing (NLP) capabilities to create new tasks based on the objective, and retrieve task results for context. " +
            " This is a pared-down version of the original Task-Driven Autonomous Agent " +
            " Agent will go against the" + 
            " set of the documents that you select here - " + (item.selected ? [...selectedTaskAgentText, item.text as string] : selectedTaskAgentText.filter(key => key !== item.text)))

        }
    };

    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const request: AskRequest = {
                question,
                approach,
                overrides: {
                    promptTemplate: promptTemplate.length === 0 ? undefined : promptTemplate,
                    promptTemplatePrefix: promptTemplatePrefix.length === 0 ? undefined : promptTemplatePrefix,
                    promptTemplateSuffix: promptTemplateSuffix.length === 0 ? undefined : promptTemplateSuffix,
                    top: retrieveCount,
                    temperature: temperature,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions,
                    chainType: String(selectedChain?.key),
                    tokenLength: tokenLength,
                    suggestFollowupQuestions: useSuggestFollowupQuestions,
                    autoSpeakAnswers: useAutoSpeakAnswers,
                    embeddingModelType: String(selectedEmbeddingItem?.key)
                }
            };
            const result = await askApi(request, String(selectedItem?.key), String(selectedIndex), 'stuff');
            //setAnswer(result);
            setAnswer([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setAnswer([result, speechUrl]);
                startSynthesis("Answer", speechUrl);
            }
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const makeApiAgentRequest = async (question: string) => {
        lastAgentQuestionRef.current = question;

        error && setAgentError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        try {
            const request: AskRequest = {
                question,
                approach,
                overrides: {
                    indexType: String(selectedindexTypeItem?.key),
                    indexes: selectedIndexes,
                    promptTemplate: promptTemplate.length === 0 ? undefined : promptTemplate,
                    promptTemplatePrefix: promptTemplatePrefix.length === 0 ? undefined : promptTemplatePrefix,
                    promptTemplateSuffix: promptTemplateSuffix.length === 0 ? undefined : promptTemplateSuffix,
                    top: retrieveCount,
                    temperature: temperature,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions,
                    chainType: String(selectedChain?.key),
                    tokenLength: tokenLength,
                    suggestFollowupQuestions: useSuggestFollowupQuestions,
                    autoSpeakAnswers: useAutoSpeakAnswers,
                    embeddingModelType: String(selectedEmbeddingItem?.key)
                }
            };
            const result = await askAgentApi(request);
            //setAgentAnswer(result);
            setAgentAnswer([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setAgentAnswer([result, speechUrl]);
                startSynthesis("AnswerAgent", speechUrl);
            }
        } catch (e) {
            setAgentError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const makeApiTaskAgentRequest = async (question: string) => {
        lastTaskAgentQuestionRef.current = question;

        error && setTaskAgentError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        try {
            const request: AskRequest = {
                question,
                approach,
                overrides: {
                    indexType: String(selectedindexTypeItem?.key),
                    indexes: selectedTaskAgentIndexes,
                    promptTemplate: promptTemplate.length === 0 ? undefined : promptTemplate,
                    promptTemplatePrefix: promptTemplatePrefix.length === 0 ? undefined : promptTemplatePrefix,
                    promptTemplateSuffix: promptTemplateSuffix.length === 0 ? undefined : promptTemplateSuffix,
                    top: retrieveCount,
                    temperature: temperature,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions,
                    chainType: String(selectedChain?.key),
                    tokenLength: tokenLength,
                    suggestFollowupQuestions: useSuggestFollowupQuestions,
                    autoSpeakAnswers: useAutoSpeakAnswers,
                    embeddingModelType: String(selectedEmbeddingItem?.key)
                }
            };
            const result = await askTaskAgentApi(request);
            setTaskAgentAnswer([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setTaskAgentAnswer([result, speechUrl]);
                startSynthesis("AnswerTaskAgent", speechUrl);
            }
        } catch (e) {
            setTaskAgentError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const startSynthesis = async (answerType: string, url: string | null) => {
        if(isSpeaking) {
            audio.pause();
            setIsSpeaking(false);
        }

        if(url === null) {
            let speechAnswer;
            if (answerType == "Answer")
                speechAnswer = answer && answer[0].answer;
            else if (answerType == "AnswerAgent")
                speechAnswer = answerAgent && answerAgent[0].answer;
            else if (answerType == "AnswerTaskAgent")
                speechAnswer = answerTaskAgent && answerTaskAgent[0].answer;

            const speechUrl = await getSpeechApi(speechAnswer || '');
            if (speechUrl === null) {
                return;
            }
            audio = new Audio(speechUrl);
            audio.play();
            setIsSpeaking(true);
            audio.addEventListener('ended', () => {
                setIsSpeaking(false);
            });

        } else {
            audio = new Audio(url);
            audio.play();
            setIsSpeaking(true);
            audio.addEventListener('ended', () => {
                setIsSpeaking(false);
            });    
        }
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItem(item);
    };

    const stopSynthesis = () => {
        audio.pause();
        setIsSpeaking(false);
    };

    const onEnableAutoSpeakAnswersChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseAutoSpeakAnswers(!!checked);
    };

    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
    };

    const onUseSuggestFollowupQuestionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSuggestFollowupQuestions(!!checked);
    };

    const onPromptTemplatePrefixChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplatePrefix(newValue || "");
    };

    const onPromptTemplateSuffixChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplateSuffix(newValue || "");
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "3"));
    };

    const onTemperatureChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTemperature(parseInt(newValue || "0.3"));
    };

    const onTokenLengthChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTokenLength(parseInt(newValue || "1000"));
    };

    const onApproachChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        setApproach((option?.key as Approaches) || Approaches.RetrieveThenRead);
    };

    const onUseSemanticRankerChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticRanker(!!checked);
    };

    const onUseSemanticCaptionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticCaptions(!!checked);
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onShowCitation = (citation: string) => {
        if (citation.indexOf('http') > -1 || citation.indexOf('https') > -1) {
            window.open(citation.replace('/content/', ''), '_blank');
        } else {
            if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab) {
                setActiveAnalysisPanelTab(undefined);
            } else {
                setActiveCitation(citation);
                setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
            }
        }
    };

    const onToggleTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab === tab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }
    };

    const refreshBlob = async () => {
        const files = []
        const indexType = []
    
        //const blobs = containerClient.listBlobsFlat(listOptions)
        const blobs = await refreshIndex()       
        for (const blob of blobs.values) {
          if (blob.embedded == "true")
          {
            files.push({
                text: blob.indexName,
                key: blob.namespace
            })
            indexType.push({
                    key:blob.namespace,
                    iType:blob.indexType,
                    summary:blob.summary,
                    qa:blob.qa == null ? '' : blob.qa
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
                setSummary(item.summary)
                setQa(item.qa)

                const sampleQuestion = []
                const  questionList = item.qa.split("\\n")
                for (const item of questionList) {
                    if ((item != '')) {
                        sampleQuestion.push({
                            text: item.replace(/[0-9]./g, ''),
                            value: item.replace(/[0-9]./g, ''),
                        })
                    } 
                }
                const generatedExamples: ExampleModel[] = sampleQuestion
                setExampleList(generatedExamples)
                setExampleLoading(false)
            }
        }
        setIndexMapping(uniqIndexType)
    }

    const clickRefreshQuestions = async () => {
        setIsQuestionPanelOpen(!isQuestionPanelOpen)
        await refreshQuestionList()
    }

    const refreshQuestionList = async () => {
        let questionList
        if (selectedIndex == undefined) {
            questionList = await refreshQuestions(selectedIndexes[0].indexName, selectedIndexes[0].indexNs)
        }
        else 
            questionList = await refreshQuestions(String(selectedIndex), String(selectedItem?.key))
        
        const sampleQuestionList = []
        for (const question of questionList.values) {
            sampleQuestionList.push({
                question: question.question,
            });    
        }
        setQuestionList(sampleQuestionList)
    }

    // const refreshQuestionsList = async (indexType:string, indexName:string) => {
    //     const questionList = await  refreshQuestions(indexType, indexName)
        
    //     const sampleQuestionList = []
    //     for (const question of questionList.values) {
    //         sampleQuestionList.push({
    //             question: question.question,
    //         });    
    //     }
    //     setQuestionList(sampleQuestionList)
    // }

    const refreshSummary = async (requestType : string) => {
        try {
            const result = await summaryAndQa(String(selectedIndex), String(selectedItem?.key), String(selectedEmbeddingItem?.key), 
            requestType, 'stuff');
            refreshBlob();
        } catch (e) {
        } finally {
        }
    }

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedItem(item);
        setAnswer(undefined)
        const defaultKey = item?.key
        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                setSelectedIndex(item.iType)
                setSummary(item.summary)
                setQa(item.qa)

                const sampleQuestion = []

                const  questionList = item.qa.split("\\n")
                for (const item of questionList) {
                    if ((item != '')) {
                        sampleQuestion.push({
                            text: item.replace(/[0-9]./g, ''),
                            value: item.replace(/[0-9]./g, ''),
                        })
                    } 
                }
                const generatedExamples: ExampleModel[] = sampleQuestion
                setExampleList(generatedExamples)
                setExampleLoading(false)

                //refreshQuestionsList(item.iType, item.key)
            }
        })
    };

    const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedChain(item);
    };

    const onTabChange = (item?: PivotItem | undefined, ev?: React.MouseEvent<HTMLElement, MouseEvent> | undefined): void => {
        if (item?.props.headerText === "Agent QA") {
            setAgentSummary("This sample shows using Agents use an LLM to determine which actions to take and in what order." + 
            " An action can either be using a tool and observing its output, or returning to the user.  Agent will go against the" + 
            " set of the documents that you select here")
        } 
        if (item?.props.headerText === "Task Agent QA") {
            setTaskAgentSummary("This sample demonstrates how to implement BabyAGI by Yohei Nakajima. BabyAGI is an AI agent that can " + 
            " generate and pretend to execute tasks based on a given objective." + 
            " It is example of an AI-powered task management system. The system uses OpenAI and creates, prioritize, and execute tasks. " + 
            " The main idea behind this system is that it creates tasks based on the result of previous tasks and a predefined objective. " +
            " The script then uses OpenAI's natural language processing (NLP) capabilities to create new tasks based on the objective, and retrieve task results for context. " +
            " This is a pared-down version of the original Task-Driven Autonomous Agent " +
            " An action can either be using a tool and observing its output, or returning to the user.  Agent will go against the" + 
            " set of the documents that you select here")
        } 
    };

    useEffect(() => {
        refreshBlob()
        setChainTypeOptions(chainType)
        setSelectedChain(chainType[0])
        setSelectedindexTypeItem(indexTypeOptions[0])
        refreshFilteredBlob(indexTypeOptions[0].key)
        setSelectedEmbeddingItem(embeddingOptions[0])
    }, [])

    const approaches: IChoiceGroupOption[] = [
        {
            key: Approaches.RetrieveThenRead,
            text: "Retrieve-Then-Read"
        }
    ];

    const onQuestionClicked = (questionFromList: any) => {
        makeApiRequest(questionFromList.question);
    }
    
    const clearChat = () => {
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswer(undefined);
    };

    const clearAgentChat = () => {
        lastAgentQuestionRef.current = "";
        errorAgent && setAgentError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAgentAnswer(undefined);
        setSelectedKeys([])
        setSelectedindexTypeItem(indexTypeOptions[0])
        setSelectedIndexes([])
    };

    const clearTaskAgentChat = () => {
        lastTaskAgentQuestionRef.current = "";
        errorTaskAgent && setTaskAgentError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setTaskAgentAnswer(undefined);

        setSelectedKeys([])
        setSelectedindexTypeItem(indexTypeOptions[0])
        setSelectedIndexes([])
    };

    return (

        <div className={styles.root}>
            <div className={styles.oneshotContainer}>
            <Pivot aria-label="QA" onLinkClick={onTabChange}>
                    <PivotItem
                        headerText="QA"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                            <div className={styles.oneshotTopSection}>
                                <div className={styles.commandsContainer}>
                                    <ClearChatButton className={styles.settingsButton} onClick={clearChat} disabled={!lastQuestionRef.current || isLoading} />
                                    <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                                    <QuestionListButton className={styles.settingsButton} onClick={() => clickRefreshQuestions()} />
                                    <div className={styles.settingsButton}>{selectedItem ? 
                                            "Document Name : "  + selectedItem.text : undefined}</div>
                                </div>
                                <h1 className={styles.oneshotTitle}>Ask your data</h1>
                                <div className={styles.example}>
                                    <p className={styles.exampleText}><b>Document Summary</b> : {summary}</p>
                                </div>
                                <br/>
                                <div className={styles.oneshotQuestionInput}>
                                    <QuestionInput
                                        placeholder="Ask me anything"
                                        updateQuestion={lastQuestionRef.current}
                                        disabled={isLoading}
                                        onSend={question => makeApiRequest(question)}
                                    />
                                </div>
                                {!answer && (<h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>)}
                                {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                                <ExampleList onExampleClicked={onExampleClicked}
                                EXAMPLES={
                                    exampleList
                                } />
                            </div>
                            <div className={styles.oneshotBottomSection}>
                                {isLoading && <Spinner label="Generating answer" />}
                                {!isLoading && answer && !error && (
                                    <div>
                                        <div className={styles.oneshotAnswerContainer}>
                                            <Stack horizontal horizontalAlign="space-between">
                                                <Answer
                                                    answer={answer[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onFollowupQuestionClicked={q => makeApiRequest(q)}
                                                    showFollowupQuestions={useSuggestFollowupQuestions}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("Answer", answer[1])}
                                                />
                                            </Stack>                               
                                        </div>
                                    </div>
                                )}
                                {error ? (
                                    <div className={styles.oneshotAnswerContainer}>
                                        <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                                    </div>
                                ) : null}
                                {activeAnalysisPanelTab && answer && (
                                    <AnalysisPanel
                                        className={styles.oneshotAnalysisPanel}
                                        activeCitation={activeCitation}
                                        onActiveTabChanged={x => onToggleTab(x)}
                                        citationHeight="600px"
                                        //answer={answer}
                                        answer={answer[0]}
                                        activeTab={activeAnalysisPanelTab}
                                    />
                                )}
                            </div>

                            <Panel
                                headerText="List of Questions for KB"
                                isOpen={isQuestionPanelOpen}
                                isBlocking={false}
                                onDismiss={() => setIsQuestionPanelOpen(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsQuestionPanelOpen(false)}>Close</DefaultButton>}
                                isFooterAtBottom={true}
                            >
                                <br/>
                                <Label>Double Click the question from the KB to get the cached answer</Label>
                                <div>
                                    <DetailsList
                                        compact={true}
                                        items={questionList || []}
                                        columns={questionListColumn}
                                        selectionMode={SelectionMode.none}
                                        getKey={(item: any) => item.key}
                                        setKey="none"
                                        constrainMode={ConstrainMode.unconstrained}
                                        onItemInvoked={(item:any) => onQuestionClicked(item)}
                                        focusZoneProps={focusZoneProps}
                                        layoutMode={DetailsListLayoutMode.justified}
                                        ariaLabelForSelectionColumn="Toggle selection"
                                        checkButtonAriaLabel="select row"
                                    />
                                </div>
                                <br/>
                                <DefaultButton onClick={refreshQuestionList}>Refresh Question</DefaultButton>
                            </Panel>

                            <Panel
                                headerText="Configure answer generation"
                                isOpen={isConfigPanelOpen}
                                isBlocking={false}
                                onDismiss={() => setIsConfigPanelOpen(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                                isFooterAtBottom={true}
                            >
                                <br/>
                                <div>
                                    <DefaultButton onClick={refreshBlob}>Refresh Docs</DefaultButton>
                                    <Dropdown
                                        selectedKey={selectedItem ? selectedItem.key : undefined}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        onChange={onChange}
                                        placeholder="Select an PDF"
                                        options={options}
                                        styles={dropdownStyles}
                                    />
                                    <Label className={styles.commandsContainer}>Index Type : {selectedIndex}</Label>
                                </div>
                                <br/>
                                <div>
                                    <Label>LLM Model</Label>
                                    <Dropdown
                                        selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                                        onChange={onEmbeddingChange}
                                        defaultSelectedKey="azureopenai"
                                        placeholder="Select an LLM Model"
                                        options={embeddingOptions}
                                        disabled={false}
                                        styles={dropdownStyles}
                                    />
                                </div>
                                <ChoiceGroup
                                    className={styles.oneshotSettingsSeparator}
                                    label="Approach"
                                    options={approaches}
                                    defaultSelectedKey={approach}
                                    onChange={onApproachChange}
                                />

                                {(approach === Approaches.RetrieveThenRead || approach === Approaches.ReadDecomposeAsk) && (
                                    <TextField
                                        className={styles.oneshotSettingsSeparator}
                                        defaultValue={promptTemplate}
                                        label="Override prompt template"
                                        multiline
                                        autoAdjustHeight
                                        onChange={onPromptTemplateChange}
                                    />
                                )}

                                {approach === Approaches.ReadRetrieveRead && (
                                    <>
                                        <TextField
                                            className={styles.oneshotSettingsSeparator}
                                            defaultValue={promptTemplatePrefix}
                                            label="Override prompt prefix template"
                                            multiline
                                            autoAdjustHeight
                                            onChange={onPromptTemplatePrefixChange}
                                        />
                                        <TextField
                                            className={styles.oneshotSettingsSeparator}
                                            defaultValue={promptTemplateSuffix}
                                            label="Override prompt suffix template"
                                            multiline
                                            autoAdjustHeight
                                            onChange={onPromptTemplateSuffixChange}
                                        />
                                    </>
                                )}

                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Retrieve this many documents from search:"
                                    min={1}
                                    max={7}
                                    defaultValue={retrieveCount.toString()}
                                    onChange={onRetrieveCountChange}
                                />
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Set the Temperature:"
                                    min={0.0}
                                    max={1.0}
                                    defaultValue={temperature.toString()}
                                    onChange={onTemperatureChange}
                                />
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Max Length (Tokens):"
                                    min={0}
                                    max={4000}
                                    defaultValue={tokenLength.toString()}
                                    onChange={onTokenLengthChange}
                                />
                                <Dropdown 
                                    label="Chain Type"
                                    onChange={onChainChange}
                                    selectedKey={selectedChain ? selectedChain.key : 'stuff'}
                                    options={chainTypeOptions}
                                    defaultSelectedKey={'stuff'}
                                    styles={dropdownStyles}
                                />
                                <Checkbox
                                    className={styles.chatSettingsSeparator}
                                    checked={useSuggestFollowupQuestions}
                                    label="Suggest follow-up questions"
                                    onChange={onUseSuggestFollowupQuestionsChange}
                                />
                                <Checkbox
                                    className={styles.chatSettingsSeparator}
                                    checked={useAutoSpeakAnswers}
                                    label="Automatically speak answers"
                                    onChange={onEnableAutoSpeakAnswersChange}
                                />
                                <br/>
                                <DefaultButton onClick={() => refreshSummary('summary')}>Regenerate Summary</DefaultButton>
                                <DefaultButton onClick={() => refreshSummary('qa')}>Regenerate Qa</DefaultButton>
                            </Panel>
                    </PivotItem>
                    <PivotItem
                        headerText="Agent QA"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                            <div className={styles.oneshotTopSection}>
                                <div className={styles.commandsContainer}>
                                    <ClearChatButton className={styles.settingsButton} onClick={clearAgentChat} disabled={!lastAgentQuestionRef.current || isLoading} />
                                    <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                                </div>
                                <div className={styles.commandsContainer}>
                                <Stack enableScopedSelectors tokens={outerStackTokens}>
                                    <Stack enableScopedSelectors  tokens={innerStackTokens}>
                                        <Stack.Item grow styles={stackItemStyles}>
                                            <DefaultButton onClick={refreshBlob}>Refresh Docs</DefaultButton>&nbsp;
                                            <Label>Index Type</Label>
                                            &nbsp;
                                            <Dropdown
                                                selectedKey={selectedindexTypeItem ? selectedindexTypeItem.key : undefined}
                                                onChange={onIndexChange}
                                                defaultSelectedKey="pinecone"
                                                placeholder="Select an Index Type"
                                                options={indexTypeOptions}
                                                disabled={false}
                                                styles={dropdownStyles}
                                            />
                                            &nbsp;
                                            <Dropdown
                                                selectedKeys={selectedKeys}
                                                // eslint-disable-next-line react/jsx-no-bind
                                                onChange={onFilteredOptionChange}
                                                placeholder="Select Your Documents"
                                                multiSelect={true}
                                                options={filteredOptions}
                                                styles={dropdownStyles}
                                            />
                                            &nbsp;
                                            <Label>LLM Model</Label>
                                            &nbsp;
                                            <Dropdown
                                                selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                                                onChange={onEmbeddingChange}
                                                defaultSelectedKey="azureopenai"
                                                placeholder="Select an LLM Model"
                                                options={embeddingOptions}
                                                disabled={false}
                                                styles={dropdownStyles}
                                            />
                                        </Stack.Item>
                                        <Stack.Item grow styles={stackItemStyles}>
                                        </Stack.Item>
                                    </Stack>
                                </Stack>
                                </div>                      
                                <h1 className={styles.oneshotTitle}>Ask your data</h1>
                                <div className={styles.example}>
                                    <p className={styles.fullText}><b>Document Summary</b> : {agentSummary}</p>
                                </div>
                                <br/>
                                <div className={styles.oneshotQuestionInput}>
                                    <QuestionInput
                                        placeholder="Ask me anything"
                                        disabled={isLoading}
                                        updateQuestion={lastAgentQuestionRef.current}
                                        onSend={question => makeApiAgentRequest(question)}
                                    />
                                </div>
                                <div className={styles.chatContainer}>
                                </div>    
                            </div>
                            <div className={styles.oneshotBottomSection}>
                                {isLoading && <Spinner label="Generating answer" />}
                                {!isLoading && answerAgent && !errorAgent && (
                                    <div>
                                        <div className={styles.oneshotAnswerContainer}>
                                            <Stack horizontal horizontalAlign="space-between">
                                                <Answer
                                                    //answer={answerAgent}
                                                    answer={answerAgent[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onFollowupQuestionClicked={q => makeApiAgentRequest(q)}
                                                    showFollowupQuestions={useSuggestFollowupQuestions}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("AnswerAgent", answerAgent[1])}
                                                />
                                            </Stack>                               
                                        </div>
                                    </div>
                                )}
                                {error ? (
                                    <div className={styles.oneshotAnswerContainer}>
                                        <AnswerError error={error.toString()} onRetry={() => makeApiAgentRequest(lastAgentQuestionRef.current)} />
                                    </div>
                                ) : null}
                                {activeAnalysisPanelTab && answerAgent && (
                                    <AnalysisPanel
                                        className={styles.oneshotAnalysisPanel}
                                        activeCitation={activeCitation}
                                        onActiveTabChanged={x => onToggleTab(x)}
                                        citationHeight="600px"
                                        //answer={answerAgent}
                                        answer={answerAgent[0]}
                                        activeTab={activeAnalysisPanelTab}
                                    />
                                )}
                            </div>

                            <Panel
                                headerText="Configure answer generation"
                                isOpen={isConfigPanelOpen}
                                isBlocking={false}
                                onDismiss={() => setIsConfigPanelOpen(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                                isFooterAtBottom={true}
                            >
                                <br/>
                                 <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Set the Temperature:"
                                    min={0.0}
                                    max={1.0}
                                    defaultValue={temperature.toString()}
                                    onChange={onTemperatureChange}
                                />
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Max Length (Tokens):"
                                    min={0}
                                    max={4000}
                                    defaultValue={tokenLength.toString()}
                                    onChange={onTokenLengthChange}
                                />
                                <Dropdown 
                                    label="Chain Type"
                                    onChange={onChainChange}
                                    selectedKey={selectedChain ? selectedChain.key : 'stuff'}
                                    options={chainTypeOptions}
                                    defaultSelectedKey={'stuff'}
                                    styles={dropdownStyles}
                                />
                                <Checkbox
                                    className={styles.chatSettingsSeparator}
                                    checked={useSuggestFollowupQuestions}
                                    label="Suggest follow-up questions"
                                    onChange={onUseSuggestFollowupQuestionsChange}
                                />
                                 <Checkbox
                                    className={styles.chatSettingsSeparator}
                                    checked={useAutoSpeakAnswers}
                                    label="Automatically speak answers"
                                    onChange={onEnableAutoSpeakAnswersChange}
                                />
                            </Panel>
                        </PivotItem>
                        <PivotItem
                        headerText="Task Agent QA"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                            <div className={styles.oneshotTopSection}>
                                <div className={styles.commandsContainer}>
                                    <ClearChatButton className={styles.settingsButton} onClick={clearTaskAgentChat} disabled={!lastTaskAgentQuestionRef.current || isLoading} />
                                    <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                                </div>
                                <div className={styles.commandsContainer}>
                                <Stack enableScopedSelectors tokens={outerStackTokens}>
                                    <Stack enableScopedSelectors  tokens={innerStackTokens}>
                                        <Stack.Item grow styles={stackItemStyles}>
                                            <DefaultButton onClick={refreshBlob}>Refresh Docs</DefaultButton>&nbsp;
                                            <Label>Index Type</Label>
                                            &nbsp;
                                            <Dropdown
                                                selectedKey={selectedindexTypeItem ? selectedindexTypeItem.key : undefined}
                                                onChange={onIndexChange}
                                                defaultSelectedKey="pinecone"
                                                placeholder="Select an Index Type"
                                                options={indexTypeOptions}
                                                disabled={false}
                                                styles={dropdownStyles}
                                            />
                                            &nbsp;
                                            <Dropdown
                                                selectedKeys={selectedTaskAgentKeys}
                                                // eslint-disable-next-line react/jsx-no-bind
                                                onChange={onFilteredTaskAgentOptionChange}
                                                placeholder="Select Your Documents"
                                                multiSelect={true}
                                                options={filteredTaskAgentOptions}
                                                styles={dropdownStyles}
                                            />
                                            &nbsp;
                                            <Label>LLM Model</Label>
                                            &nbsp;
                                            <Dropdown
                                                selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                                                onChange={onEmbeddingChange}
                                                defaultSelectedKey="azureopenai"
                                                placeholder="Select an LLM Model"
                                                options={embeddingOptions}
                                                disabled={false}
                                                styles={dropdownStyles}
                                            />
                                        </Stack.Item>
                                    </Stack>
                                </Stack>
                                </div>                      
                                <h1 className={styles.oneshotTitle}>Task your data</h1>
                                <div className={styles.example}>
                                    <p className={styles.fullText}><b>Document Summary</b> : {taskAgentSummary}</p>
                                </div>
                                <br/>
                                <div className={styles.oneshotQuestionInput}>
                                    <QuestionInput
                                        placeholder="Ask me anything"
                                        disabled={isLoading}
                                        updateQuestion={lastTaskAgentQuestionRef.current}
                                        onSend={question => makeApiTaskAgentRequest(question)}
                                    />
                                </div>
                                <div className={styles.chatContainer}>
                                </div>    
                            </div>
                            <div className={styles.oneshotBottomSection}>
                                {isLoading && <Spinner label="Generating answer" />}
                                {!isLoading && answerTaskAgent && !errorTaskAgent && (
                                    <div>
                                        <div className={styles.oneshotAnswerContainer}>
                                            <Stack horizontal horizontalAlign="space-between">
                                                <Answer
                                                    answer={answerTaskAgent[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onFollowupQuestionClicked={q => makeApiTaskAgentRequest(q)}
                                                    showFollowupQuestions={useSuggestFollowupQuestions}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("AnswerTaskAgent", answerTaskAgent[1])}
                                                />
                                            </Stack>                               
                                        </div>
                                    </div>
                                )}
                                {error ? (
                                    <div className={styles.oneshotAnswerContainer}>
                                        <AnswerError error={error.toString()} onRetry={() => makeApiTaskAgentRequest(lastTaskAgentQuestionRef.current)} />
                                    </div>
                                ) : null}
                                {activeAnalysisPanelTab && answerTaskAgent && (
                                    <AnalysisPanel
                                        className={styles.oneshotAnalysisPanel}
                                        activeCitation={activeCitation}
                                        onActiveTabChanged={x => onToggleTab(x)}
                                        citationHeight="600px"
                                        answer={answerTaskAgent[0]}
                                        activeTab={activeAnalysisPanelTab}
                                    />
                                )}
                            </div>

                            <Panel
                                headerText="Configure answer generation"
                                isOpen={isConfigPanelOpen}
                                isBlocking={false}
                                onDismiss={() => setIsConfigPanelOpen(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                                isFooterAtBottom={true}
                            >
                                <br/>
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Maximum number of Task Iterations:"
                                    min={1}
                                    max={5}
                                    defaultValue={retrieveCount.toString()}
                                    onChange={onRetrieveCountChange}
                                />
                                 <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Set the Temperature:"
                                    min={0.0}
                                    max={1.0}
                                    defaultValue={temperature.toString()}
                                    onChange={onTemperatureChange}
                                />
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Max Length (Tokens):"
                                    min={0}
                                    max={4000}
                                    defaultValue={tokenLength.toString()}
                                    onChange={onTokenLengthChange}
                                />
                                <Dropdown 
                                    label="Chain Type"
                                    onChange={onChainChange}
                                    selectedKey={selectedChain ? selectedChain.key : 'stuff'}
                                    options={chainTypeOptions}
                                    defaultSelectedKey={'stuff'}
                                    styles={dropdownStyles}
                                />
                                <Checkbox
                                    className={styles.chatSettingsSeparator}
                                    checked={useSuggestFollowupQuestions}
                                    label="Suggest follow-up questions"
                                    onChange={onUseSuggestFollowupQuestionsChange}
                                />
                                 <Checkbox
                                    className={styles.chatSettingsSeparator}
                                    checked={useAutoSpeakAnswers}
                                    label="Automatically speak answers"
                                    onChange={onEnableAutoSpeakAnswersChange}
                                />
                            </Panel>
                        </PivotItem>
                </Pivot>
            </div>
        </div>
    );
};

export default OneShot;

