import { useRef, useState, useEffect, useMemo } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, Spinner, Stack, ChoiceGroup, IChoiceGroupOption } from "@fluentui/react";
import { SparkleFilled } from "@fluentui/react-icons";
import { ShieldLockRegular } from "@fluentui/react-icons";

import { Dropdown, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import styles from "./VideoGpt.module.css";
import { Label } from '@fluentui/react/lib/Label';
import { ExampleList, ExampleModel } from "../../components/Example";

import { chat, Approaches, AskResponse, ChatRequest, ChatTurn, refreshVideoIndex, askApi, AskRequest, 
    getSpeechApi, chatGpt, SearchTypes,
    getAllIndexSessions, getIndexSession, getIndexSessionDetail, refreshQuestions, renameIndexSession, getUserInfo } from "../../api";
import { Answer, AnswerError, AnswerLoading } from "../../components/Answer";
import { AnswerChat } from "../../components/Answer/AnswerChat";
import { QuestionInput } from "../../components/QuestionInput";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ClearChatButton } from "../../components/ClearChatButton";
import { SettingsButton } from "../../components/SettingsButton";
import { ChatSession } from "../../api/models";
import { DetailsList, DetailsListLayoutMode, SelectionMode, Selection, ConstrainMode} from '@fluentui/react/lib/DetailsList';
import { SessionButton } from "../../components/SessionButton";
import { MarqueeSelection } from '@fluentui/react/lib/MarqueeSelection';
import { RenameButton } from "../../components/RenameButton";
import { Pivot, PivotItem } from '@fluentui/react';
import { QuestionListButton } from "../../components/QuestionListButton/QuestionListButton";
import { mergeStyleSets } from '@fluentui/react/lib/Styling';

var audio = new Audio();

const VideoGpt = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(true);
    const [useAutoSpeakAnswers, setUseAutoSpeakAnswers] = useState<boolean>(false);
    const [searchTypeOptions, setSearchTypeOptions] = useState<SearchTypes>(SearchTypes.Similarity);
    const [isQuestionPanelOpen, setIsQuestionPanelOpen] = useState(false);
    const [questionList, setQuestionList] = useState<any[]>();
    const [selectedIndexes, setSelectedIndexes] = useState<{ indexNs: string; indexName: any; returnDirect: string; }[]>([]);
    const [answer, setAnswer] = useState<[AskResponse, string | null]>();
    const [approach, setApproach] = useState<Approaches>(Approaches.RetrieveThenRead);
    const [qaAnswer, setQaAnswer] = useState<[AskResponse, string | null]>();

    const [options, setOptions] = useState<any>([])
    const [temperature, setTemperature] = useState<number>(0.3);
    const [tokenLength, setTokenLength] = useState<number>(500);

    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };

    const lastQuestionRef = useRef<string>("");
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    const [runningIndex, setRunningIndex] = useState<number>(-1);
    
    const [chatSession, setChatSession] = useState<ChatSession | null>(null);
    const [sessionId, setSessionId] = useState<string>();
    const [sessionList, setSessionList] = useState<any[]>();
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplatePrefix, setPromptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix, setPromptTemplateSuffix] = useState<string>("");
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

    const [exampleLoading, setExampleLoading] = useState(false)

    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; chunkSize:string; chunkOverlap:string; promptType:string }[]>();
    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [summary, setSummary] = useState<string>();

    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const [selectedItems, setSelectedItems] = useState<any[]>([]);
    const [sessionName, setSessionName] = useState<string>('');
    const [oldSessionName, setOldSessionName] = useState<string>('');
    const [showAuthMessage, setShowAuthMessage] = useState<boolean>(false);
    const [selectedDeploymentType, setSelectedDeploymentType] = useState<IDropdownOption>();
    const [selectedPromptTypeItem, setSelectedPromptTypeItem] = useState<IDropdownOption>();
    const [selectedChunkSize, setSelectedChunkSize] = useState<string>()
    const [selectedChunkOverlap, setSelectedChunkOverlap] = useState<string>()
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();
    const [chainTypeOptions, setChainTypeOptions] = useState<any>([])

    const generateQuickGuid = () => {
        return Math.random().toString(36).substring(2, 15) +
            Math.random().toString(36).substring(2, 15);
    }

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
            key: 'financialtable',
            text: 'financialtable'
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

    const searchTypes: IChoiceGroupOption[] = [
        {
            key: SearchTypes.Similarity,
            text: "Similarity"
        },
        {
            key: SearchTypes.Hybrid,
            text: "Hybrid"
        },
        {
            key: SearchTypes.HybridReRank,
            text: "Hybrid with ReRank"
        }
    ];

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
    
    const sessionListColumn = [
        {
          key: 'Session Name',
          name: 'Session Name',
          fieldName: 'Session Name',
          minWidth: 100,
          maxWidth: 200, 
          isResizable: false,
        }
    ]

    const chainType = [
        { key: 'stuff', text: 'Stuff'},
        { key: 'map_rerank', text: 'Map ReRank' },
        { key: 'map_reduce', text: 'Map Reduce' },
        { key: 'refine', text: 'Refine'},
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

    const getUserInfoList = async () => {
        const userInfoList = await getUserInfo();
        if (userInfoList.length === 0 && window.location.hostname !== "localhost") {
            setShowAuthMessage(true);
        }
        else {
            setShowAuthMessage(false);
        }
    }

    const detailsList = useMemo(
        () => (
            <MarqueeSelection selection={selection}>
                <DetailsList
                    className={styles.example}
                    items={sessionList || []}
                    columns={sessionListColumn}
                    selectionMode={SelectionMode.single}
                    getKey={(item: any) => item.key}
                    setKey="single"
                    onActiveItemChanged={(item:any) => onSessionClicked(item)}
                    layoutMode={DetailsListLayoutMode.fixedColumns}
                    ariaLabelForSelectionColumn="Toggle selection"
                    checkButtonAriaLabel="select row"
                    selection={selection}
                    selectionPreservedOnEmptyClick={false}
                 />
             </MarqueeSelection>
         ),
         [selection, sessionListColumn, sessionList]
     );

    const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedChain(item);
    };

    const makeApiRequest = async (question: string) => {
        let  currentSession = chatSession;
        let firstSession = false;
        if (!lastQuestionRef.current || currentSession === null) {
            currentSession = handleNewConversation();
            firstSession = true;
            let sessionLists = sessionList;
            sessionLists?.unshift({
                "Session Name": currentSession.sessionId,
            });
            setSessionList(sessionLists)
        }
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const history: ChatTurn[] = answers.map(a => ({ user: a[0], bot: a[1].answer }));
            const request: ChatRequest = {
                history: [...history, { user: question, bot: undefined }],
                approach: Approaches.ReadRetrieveRead,
                overrides: {
                    promptTemplate: promptTemplate.length === 0 ? undefined : promptTemplate,
                    excludeCategory: excludeCategory.length === 0 ? undefined : excludeCategory,
                    top: retrieveCount,
                    temperature: temperature,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions,
                    suggestFollowupQuestions: useSuggestFollowupQuestions,
                    tokenLength: tokenLength,
                    autoSpeakAnswers: useAutoSpeakAnswers,
                    embeddingModelType: String(selectedEmbeddingItem?.key),
                    firstSession: firstSession,
                    session: JSON.stringify(currentSession),
                    sessionId: currentSession.sessionId,
                    deploymentType: String(selectedDeploymentType?.key),
                    chainType: String(selectedChain?.key),
                    searchType: searchTypeOptions,
                }
            };
            const result = await chat(request, String(selectedItem?.key), String(selectedIndex));
            //setAnswers([...answers, [question, result]]);
            setAnswers([...answers, [question, result, null]]);
            if(useAutoSpeakAnswers){
                const speechUrl = await getSpeechApi(result.answer);
                setAnswers([...answers, [question, result, speechUrl]]);
                startOrStopSynthesis("gpt35", speechUrl, answers.length);
            }
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const getCosmosSession = async (indexNs : string, indexType: string) => {

        try {
            await getAllIndexSessions(indexNs, indexType, 'chat', 'Session')
            .then(async (response:any) => {
                const sessionLists = []
                if (response.length === 0) {
                    sessionLists.push({
                        "Session Name": "No Sessions found",
                    });    
                } else 
                {
                    for (const session of response) {
                        sessionLists.push({
                            "Session Name": session.name,
                        });    
                    }
                }
                setSessionList(sessionLists)
            })
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setChatSession(null)
        setAnswers([]);
        setQaAnswer(undefined);
        setSelectedItems([])
        setSessionName('');
    };

    const renameSession = async () => {
        //const oldSessionName = String(selectedItems[0]?.['Session Name'])
        if (oldSessionName === 'No Sessions found' || oldSessionName === undefined || sessionName === "" || sessionName === undefined
        || oldSessionName === "" || sessionName === 'No Sessions found') {
            alert("Select valid session to rename")
        }
        else {
            await renameIndexSession(oldSessionName, sessionName)
                .then(async (sessionResponse:any) => {
                    const defaultKey = selectedItem?.key
                    indexMapping?.findIndex((item) => {
                        if (item.key == defaultKey) {
                            getCosmosSession(item?.key, item?.iType)
                        }
                    })
                    clearChat();
            })
        }
    };
    const onSessionNameChange = (event: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        const oldSessionName = String(selectedItems[0]?.['Session Name'])
        if (newValue === undefined || newValue === "") {
            alert("Provide session name")
        }
        setSessionName(newValue || oldSessionName);
    };

    const onEnableAutoSpeakAnswersChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseAutoSpeakAnswers(!!checked);
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onSearchTypeChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        setSearchTypeOptions((option?.key as SearchTypes) || SearchTypes.Similarity);
    };

    const startOrStopSynthesis = async (answerType:string, url: string | null, index: number) => {
        if(runningIndex === index) {
            audio.pause();
            setRunningIndex(-1);
            return;
        }

        if(runningIndex !== -1) {
            audio.pause();
            setRunningIndex(-1);
        }

        if(url === null) {
            let speechAnswer;
            if (answerType === 'gpt35') {
                answers.map((answer, index) => {
                    speechAnswer = answer[1].answer
                })                
            }
            const speechUrl = await getSpeechApi(speechAnswer || '');
            if (speechUrl === null) {
                return;
            }
            audio = new Audio(speechUrl);
            audio.play();
            setRunningIndex(index);
            audio.addEventListener('ended', () => {
                setRunningIndex(-1);
            });
        } else {
            audio = new Audio(url);
            audio.play();
            setRunningIndex(index);
            audio.addEventListener('ended', () => {
                setRunningIndex(-1);
            });
        }
    };

    const refreshVideoBlob = async () => {
        const files = []
        const indexType = []

        const blobs = await refreshVideoIndex()       
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
                    //summary:blob.summary,
                    //qa:blob.qa,
                    chunkSize:blob.chunkSize,
                    chunkOverlap:blob.chunkOverlap,
                    promptType:blob.promptType
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
                //setSummary(item.summary)
                //setQa(item.qa)
                setSelectedChunkOverlap(item.chunkOverlap)
                setSelectedChunkSize(item.chunkSize)
                //setSelectedPromptType(item.promptType)
                setSelectedPromptTypeItem(promptTypeOptions.find(x => x.key === item.promptType))
                updatePrompt(item.promptType)

                if (Number(item.chunkSize) > 4000) {
                    setSelectedDeploymentType(deploymentTypeOptions[1])
                } else {
                    setSelectedDeploymentType(deploymentTypeOptions[0])
                }

                getCosmosSession(item?.key, item?.iType)

                //const sampleQuestion = []
                // const  questionList = item.qa.split("\\n")
                // for (const item of questionList) {
                //     if ((item != '')) {
                //         sampleQuestion.push({
                //             text: item.replace(/^\d+\.\s*/, '').replace('<', '').replace('>', ''),
                //             value: item.replace(/^\d+\.\s*/, '').replace('<', '').replace('>', '')
                //         })
                //     } 
                // }
                // const generatedExamples: ExampleModel[] = sampleQuestion
                // setExampleList(generatedExamples)
                // setExampleLoading(false)
            }
        }
        setIndexMapping(uniqIndexType)
    }

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedItem(item);
        clearChat();

        const defaultKey = item?.key
        let indexType = 'pinecone'

        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                indexType = item.iType
                setSelectedIndex(item.iType)
                setSelectedChunkSize(item.chunkSize)
                setSelectedChunkOverlap(item.chunkOverlap)
                // setSelectedPromptType(item.promptType)
                setSelectedPromptTypeItem(promptTypeOptions.find(x => x.key === item.promptType))
                updatePrompt(item.promptType)

                if (Number(item.chunkSize) > 4000) {
                    setSelectedDeploymentType(deploymentTypeOptions[1])
                } else {
                    setSelectedDeploymentType(deploymentTypeOptions[0])
                }

                getCosmosSession(item?.key, item?.iType)
            }
        })
    };

    const onSessionClicked = async (sessionFromList: any) => {
        //makeApiRequest(sessionFromList.name);
        const sessionName = sessionFromList["Session Name"]
        setSessionName(sessionName)
        setOldSessionName(sessionName)
        if (sessionName != "No Session Found") {
            try {
                await getIndexSession(String(selectedItem?.key), String(selectedIndex), sessionName)
                .then(async (sessionResponse:any) => {
                    const sessionId = sessionResponse[0].sessionId
                    const newSession: ChatSession = {
                        id: sessionResponse[0].id,
                        type: sessionResponse[0].type,
                        sessionId: sessionResponse[0].sessionId,
                        name: sessionResponse[0].name,
                        chainType: sessionResponse[0].chainType,
                        feature: sessionResponse[0].feature,
                        indexId: sessionResponse[0].indexId,
                        indexType: sessionResponse[0].indexType,
                        indexName: sessionResponse[0].indexName,
                        llmModel: sessionResponse[0].llmModel,
                        timestamp: sessionResponse[0].timestamp,
                        tokenUsed: sessionResponse[0].tokenUsed,
                        embeddingModelType: sessionResponse[0].embeddingModelType
                      };
                    setChatSession(newSession);
                    await getIndexSessionDetail(sessionId)
                    .then(async (response:any) => {
                        const rows = response.reduce(function (rows: any[][], key: any, index: number) { 
                            return (index % 2 == 0 ? rows.push([key]) 
                            : rows[rows.length-1].push(key)) && rows;
                        }, []);
                        const sessionLists: [string, AskResponse, string | null][] = [];
                        for (const session of rows)
                        {
                            sessionLists.push([session[0].content, session[1].content, null]);
                        }
                        lastQuestionRef.current = sessionLists[sessionLists.length - 1][0];
                        setAnswers(sessionLists);
                    })
                })
            } catch (e) {
                setError(e);
            } finally {
                setIsLoading(false);
            }
        }
    }

    const updatePrompt = (promptType: string) => {
        const genericPrompt = `Given the following extracted parts of a long document and a question, create a final answer. 
        If you don't know the answer, just say that you don't know. Don't try to make up an answer. 
        If the answer is not contained within the text below, say \"I don't know\".

        {summaries}
        Question: {question}
        `

        const medicalPrompt = `You are an AI assistant tasked with answering questions and summarizing information from medical records documents. 
        Your answer should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive information that includes details such as patient information, medical history, 
        allergies, chronic conditions, previous surgeries, prescribed medications, and upcoming appointments. 
        Ensure that it is easy to understand for healthcare professionals and provides an accurate representation of the patient's medical history 
        and current health status. 
        
        Begin with a brief introduction of the patient, followed by the main points of their medical records.
        Please remember to use clear language and maintain the integrity of the original information without missing any important details
        {summaries}
        Question: {question}
        `

        const financialPrompt = `You are an AI assistant tasked with answering questions and summarizing information from 
        earning call transcripts, annual reports, SEC filings and financial statements.
        Your answer should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive information that includes details such as reporting year and amount in millions.
        Ensure that it is easy to understand for business professionals and provides an accurate representation of the financial statement history. 
        
        Please remember to use clear language and maintain the integrity of the original information without missing any important details

        QUESTION: {question}
        =========
        {summaries}
        =========
        `

        const financialTablePrompt = `You are an AI assistant tasked with answering questions and summarizing information from 
        financial statements like income statement, cashflow and balance sheets. 
        Additionally you may also be asked to answer questions about financial ratios and other financial metrics.
        The data that you are presented will be in table format or structure.
        Your answer should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please generate a concise and comprehensive information that includes details such as reporting year and amount in millions.
        Ensure that it is easy to understand for business professionals and provides an accurate representation of the financial statement history. 
        
        Please remember to use clear language and maintain the integrity of the original information without missing any important details

        QUESTION: {question}
        =========
        {summaries}
        =========
        `

        const prospectusPrompt = `"""You are an AI assistant tasked with summarizing documents from large documents that contains information about Initial Public Offerings. 
        IPO document contains sections with information about the company, its business, strategies, risk, management structure, financial, and other information.
        Your summary should accurately capture the key information in the document while avoiding the omission of any domain-specific words. 
        Please remember to use clear language and maintain the integrity of the original information without missing any important details:
        QUESTION: {question}
        =========
        {summaries}
        =========

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
        } else if (promptType == "financialtable") {
            setPromptTemplate(financialTablePrompt)
        } else if (promptType == "prospectus") {
            setPromptTemplate(prospectusPrompt)
        } else if (promptType == "productdocmd") {
            setPromptTemplate(productDocMdPrompt)
        } else if (promptType == "custom") {
            setPromptTemplate("")
        }
    }
   
    useEffect(() => {
        if (window.location.hostname != "localhost") {
            getUserInfoList();
            setShowAuthMessage(true)
        } else
            setShowAuthMessage(false)

        setOptions([])
        refreshVideoBlob()
        setChainTypeOptions(chainType)
        setSelectedChain(chainType[0])
        setSelectedEmbeddingItem(embeddingOptions[0])
        setSelectedDeploymentType(deploymentTypeOptions[0])
        setSelectedPromptTypeItem(promptTypeOptions[0])
        getCosmosSession(String(selectedItem?.key), String(selectedIndex))
    }, [])


    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "3"));
    };

    const onUseSuggestFollowupQuestionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSuggestFollowupQuestions(!!checked);
    };

    const onTemperatureChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTemperature(parseInt(newValue || "0.3"));
    };

    const onTokenLengthChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTokenLength(parseInt(newValue || "500"));
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItem(item);
    };
    
    const onShowCitation = (citation: string, index: number) => {
        if (citation.indexOf('http') > -1 || citation.indexOf('https') > -1) {
            window.open(citation.replace('/content/', '').trim(), '_blank');
        } else {
            if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab && selectedAnswer === index) {
                setActiveAnalysisPanelTab(undefined);
            } else {
                setActiveCitation(citation);
                setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
            }
        }
        setSelectedAnswer(index);
    };

    const handleNewConversation = () => {
        const sessId = generateQuickGuid(); //uuidv4();
        setSessionId(sessId);

        const newSession: ChatSession = {
          id: generateQuickGuid(),
          type: 'Session',
          sessionId: sessId,
          name: sessId,
          chainType: 'stuff',
          feature: 'chat',
          indexId: String(selectedItem?.key),
          indexType: String(selectedIndex),
          indexName: String(selectedItem?.text),
          llmModel: 'gpt3.5',
          timestamp: String(new Date().getTime()),
          tokenUsed: 0,
          embeddingModelType: String(selectedEmbeddingItem?.key)
        };
        setChatSession(newSession);
        return newSession;
    };

    const onDeploymentTypeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedDeploymentType(item);
    };

    const onPromptTypeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedPromptTypeItem(item);
        updatePrompt(String(item?.key));
    };

    const onTabChange = (item?: PivotItem | undefined, ev?: React.MouseEvent<HTMLElement, MouseEvent> | undefined): void => {
        if (item?.props.headerText === "Chat On Data") {
            getCosmosSession(String(selectedItem?.key), String(selectedIndex))
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

    const questionListColumn = [
        {
          key: 'question',
          name: 'Question',
          fieldName: 'question',
          minWidth: 100, maxWidth: 200, isResizable: true
        }
    ]

    const clickRefreshQuestions = async () => {
        setIsQuestionPanelOpen(!isQuestionPanelOpen)
        await refreshQuestionList()
    }

    const startSynthesis = async (answerType: string, url: string | null) => {
        if(isSpeaking) {
            audio.pause();
            setIsSpeaking(false);
        }

        if(url === null) {
            let speechAnswer;
            speechAnswer = answer && answer[0].answer;

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

    const makeQaApiRequest = async (question: string) => {
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
                    embeddingModelType: String(selectedEmbeddingItem?.key),
                    deploymentType: String(selectedDeploymentType?.key),
                    searchType: searchTypeOptions,
                }
            };
            const result = await askApi(request, String(selectedItem?.key), String(selectedIndex), 'stuff');
            //setAnswer(result);
            setQaAnswer([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setQaAnswer([result, speechUrl]);
                startSynthesis("Answer", speechUrl);
            }
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const onShowQaCitation = (citation: string) => {
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

    const onToggleQaTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab === tab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }
    };

    const onQuestionClicked = (questionFromList: any) => {
        makeQaApiRequest(questionFromList.question);
    }

    const stopSynthesis = () => {
        audio.pause();
        setIsSpeaking(false);
    };

    return (
        <div className={styles.root}>
            {showAuthMessage ? (
                <Stack className={styles.chatEmptyState}>
                    <ShieldLockRegular className={styles.chatIcon} style={{color: 'darkorange', height: "200px", width: "200px"}}/>
                    <h1 className={styles.chatEmptyStateTitle}>Authentication Not Configured</h1>
                    <h2 className={styles.chatEmptyStateSubtitle}>
                        This app does not have authentication configured. Please add an identity provider by finding your app in the 
                        <a href="https://portal.azure.com/" target="_blank"> Azure Portal </a>
                        and following 
                         <a href="https://learn.microsoft.com/en-us/azure/app-service/scenario-secure-app-authentication-app-service#3-configure-authentication-and-authorization" target="_blank"> these instructions</a>.
                    </h2>
                    <h2 className={styles.chatEmptyStateSubtitle} style={{fontSize: "20px"}}><strong>Authentication configuration takes a few minutes to apply. </strong></h2>
                    <h2 className={styles.chatEmptyStateSubtitle} style={{fontSize: "20px"}}><strong>If you deployed in the last 10 minutes, please wait and reload the page after 10 minutes.</strong></h2>
                </Stack>
            ) : (
                <Pivot aria-label="ChatGpt" onLinkClick={onTabChange}>
                    <PivotItem
                        headerText="QA"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                            <div className={styles.oneshotTopSection}>
                                <div className={styles.commandsContainer}>
                                    <ClearChatButton className={styles.settingsButton}  text="Clear chat" onClick={clearChat} disabled={!lastQuestionRef.current || isLoading} />
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
                                        onSend={question => makeQaApiRequest(question)}
                                    />
                                </div>
                                {!qaAnswer && (<h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>)}
                                {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                                <ExampleList onExampleClicked={onExampleClicked}
                                EXAMPLES={
                                    exampleList
                                } />
                            </div>
                            <div className={styles.oneshotBottomSection}>
                                {isLoading && <Spinner label="Generating answer" />}
                                {!isLoading && qaAnswer && !error && (
                                    <div>
                                        <div className={styles.oneshotAnswerContainer}>
                                            <Stack horizontal horizontalAlign="space-between">
                                                <Answer
                                                    answer={qaAnswer[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowQaCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleQaTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleQaTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onFollowupQuestionClicked={q => makeQaApiRequest(q)}
                                                    showFollowupQuestions={useSuggestFollowupQuestions}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("Answer", qaAnswer[1])}
                                                />
                                            </Stack>                               
                                        </div>
                                    </div>
                                )}
                                {error ? (
                                    <div className={styles.oneshotAnswerContainer}>
                                        <AnswerError error={error.toString()} onRetry={() => makeQaApiRequest(lastQuestionRef.current)} />
                                    </div>
                                ) : null}
                                {activeAnalysisPanelTab && qaAnswer && (
                                    <AnalysisPanel
                                        className={styles.oneshotAnalysisPanel}
                                        activeCitation={activeCitation}
                                        onActiveTabChanged={x => onToggleQaTab(x)}
                                        citationHeight="600px"
                                        //answer={answer}
                                        answer={qaAnswer[0]}
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
                                <Label>Click the question from the KB to get the cached answer</Label>
                                <div>
                                    <DetailsList
                                        compact={true}
                                        items={questionList || []}
                                        columns={questionListColumn}
                                        selectionMode={SelectionMode.none}
                                        getKey={(item: any) => item.key}
                                        setKey="none"
                                        constrainMode={ConstrainMode.unconstrained}
                                        onActiveItemChanged={(item:any) => onQuestionClicked(item)}
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
                                    <DefaultButton onClick={refreshVideoBlob}>Refresh Docs</DefaultButton>
                                    <Dropdown
                                        selectedKey={selectedItem ? selectedItem.key : undefined}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        onChange={onChange}
                                        placeholder="Select an PDF"
                                        options={options}
                                        styles={dropdownStyles}
                                    />
                                    <Label className={styles.commandsContainer}>Index Type : {selectedIndex}</Label>
                                    <Label className={styles.commandsContainer}>Chunk Size : {selectedChunkSize} / Chunk Overlap : {selectedChunkOverlap}</Label>
                                </div>
                                <div>
                                    <Label>LLM Model</Label>
                                    <Dropdown
                                        selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                                        onChange={onEmbeddingChange}
                                        placeholder="Select an LLM Model"
                                        options={embeddingOptions}
                                        disabled={false}
                                        styles={dropdownStyles}
                                    />
                                </div>
                                <div>
                                    <Label>Deployment Type</Label>
                                    <Dropdown
                                            selectedKey={selectedDeploymentType ? selectedDeploymentType.key : undefined}
                                            onChange={onDeploymentTypeChange}
                                            placeholder="Select an Deployment Type"
                                            options={deploymentTypeOptions}
                                            disabled={((selectedEmbeddingItem?.key == "openai" ? true : false) || (Number(selectedChunkSize) > 4000 ? true : false))}
                                            styles={dropdownStyles}
                                    />
                                </div>
                                <div>
                                    <Label>Prompt Type</Label>
                                    <Dropdown
                                            selectedKey={selectedPromptTypeItem ? selectedPromptTypeItem.key : undefined}
                                            onChange={onPromptTypeChange}
                                            placeholder="Prompt Type"
                                            options={promptTypeOptions}
                                            disabled={false}
                                            styles={dropdownStyles}
                                    />
                                    <TextField
                                        className={styles.oneshotSettingsSeparator}
                                        value={promptTemplate}
                                        label="Override prompt template"
                                        multiline
                                        autoAdjustHeight
                                        onChange={onPromptTemplateChange}
                                    />
                                </div>
                                <ChoiceGroup
                                    className={styles.oneshotSettingsSeparator}
                                    label="Search Type"
                                    options={searchTypes}
                                    defaultSelectedKey={searchTypeOptions}
                                    onChange={onSearchTypeChange}
                                />

                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Document to Retrieve from search:"
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
                            </Panel>
                    </PivotItem>
                    <PivotItem
                        headerText="Chat On Data"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                    <div className={styles.root}>
                        <br/>
                        <div className={styles.commandsContainer}>
                            <ClearChatButton className={styles.commandButton} onClick={clearChat}  text="Clear chat" disabled={!lastQuestionRef.current || isLoading} />
                            <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            <div className={styles.commandButton}>{selectedItem ? 
                                "Document Name : "  + selectedItem.text : undefined}</div>
                        </div>
                        <div className={styles.commandsContainer}>
                            <SessionButton className={styles.commandButton} onClick={clearChat} />
                            {/* <ClearChatButton className={styles.commandButton} onClick={deleteSession}  text="Delete Session" disabled={false} /> */}
                            <RenameButton className={styles.commandButton}  onClick={renameSession}  text="Rename Session"/>
                            <TextField className={styles.commandButton} value={sessionName} onChange={onSessionNameChange}
                                styles={{root: {width: '200px'}}} />
                        </div>
                        <div className={styles.chatRoot}>
                            {detailsList}
                            <div className={styles.chatContainer}>
                                {!lastQuestionRef.current ? (
                                    <div className={styles.chatEmptyState}>
                                        <SparkleFilled fontSize={"30px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" />
                                        <h3 className={styles.chatEmptyStateTitle}>Chat with your data</h3>
                                        <div className={styles.example}>
                                            <p className={styles.exampleText}><b>Document Summary</b> : {summary}</p>
                                        </div>
                                        <h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>
                                        <div className={styles.chatInput}>
                                            <QuestionInput
                                                clearOnSend
                                                placeholder="Type a new question"
                                                disabled={isLoading}
                                                onSend={question => makeApiRequest(question)}
                                            />
                                        </div>
                                        {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                                        <ExampleList onExampleClicked={onExampleClicked}
                                        EXAMPLES={
                                            exampleList
                                        } />
                                    </div>
                                ) : (
                                    <div className={styles.chatMessageStream}>
                                        {answers.map((answer, index) => (
                                            <div key={index}>
                                                <UserChatMessage message={answer[0]} />
                                                <div className={styles.chatMessageGpt}>
                                                    <Answer
                                                        key={index}
                                                        answer={answer[1]}
                                                        isSpeaking = {runningIndex === index}
                                                        isSelected={selectedAnswer === index && activeAnalysisPanelTab !== undefined}
                                                        onCitationClicked={c => onShowCitation(c, index)}
                                                        onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab, index)}
                                                        onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab, index)}
                                                        onFollowupQuestionClicked={q => makeApiRequest(q)}
                                                        onSpeechSynthesisClicked={() => startOrStopSynthesis("gpt35", answer[2], index)}
                                                        showFollowupQuestions={useSuggestFollowupQuestions && answers.length - 1 === index}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                        {isLoading && (
                                            <>
                                                <UserChatMessage message={lastQuestionRef.current} />
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerLoading />
                                                </div>
                                            </>
                                        )}
                                        {error ? (
                                            <>
                                                <UserChatMessage message={lastQuestionRef.current} />
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                                                </div>
                                            </>
                                        ) : null}
                                        <div ref={chatMessageStreamEnd} />
                                        <div className={styles.chatInput}>
                                            <QuestionInput
                                                clearOnSend
                                                placeholder="Type a new question"
                                                disabled={isLoading}
                                                onSend={question => makeApiRequest(question)}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {answers.length > 0 && activeAnalysisPanelTab && (
                                <AnalysisPanel
                                    className={styles.chatAnalysisPanel}
                                    activeCitation={activeCitation}
                                    onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                                    citationHeight="810px"
                                    answer={answers[selectedAnswer][1]}
                                    activeTab={activeAnalysisPanelTab}
                                />
                            )}

                            <Panel
                                headerText="Configure Chat Interaction"
                                isOpen={isConfigPanelOpen}
                                isBlocking={false}
                                onDismiss={() => setIsConfigPanelOpen(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                                isFooterAtBottom={true}
                            >
                                <br/>
                                <div>
                                    <DefaultButton onClick={refreshVideoBlob}>Refresh Docs</DefaultButton>
                                    <Dropdown
                                        selectedKey={selectedItem ? selectedItem.key : undefined}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        onChange={onChange}
                                        placeholder="Select an PDF"
                                        options={options}
                                        styles={dropdownStyles}
                                    />
                                    &nbsp;
                                    <Label className={styles.commandsContainer}>Index Type : {selectedIndex}</Label>
                                    <Label className={styles.commandsContainer}>Chunk Size : {selectedChunkSize} / Chunk Overlap : {selectedChunkOverlap}</Label>
                                </div>
                                <br/>
                                <div>
                                    <Label>LLM Model</Label>
                                    <Dropdown
                                        selectedKey={selectedEmbeddingItem ? selectedEmbeddingItem.key : undefined}
                                        onChange={onEmbeddingChange}
                                        placeholder="Select an LLM Model"
                                        options={embeddingOptions}
                                        disabled={false}
                                        styles={dropdownStyles}
                                    />
                                </div>
                                <div>
                                    <Label>Deployment Type</Label>
                                    <Dropdown
                                            selectedKey={selectedDeploymentType ? selectedDeploymentType.key : undefined}
                                            onChange={onDeploymentTypeChange}
                                            placeholder="Select an Deployment Type"
                                            options={deploymentTypeOptions}
                                            disabled={((selectedEmbeddingItem?.key == "openai" ? true : false) || (Number(selectedChunkSize) > 4000 ? true : false))}
                                            styles={dropdownStyles}
                                    />
                                </div>
                                <div>
                                    <Label>Prompt Type</Label>
                                    <Dropdown
                                            selectedKey={selectedPromptTypeItem ? selectedPromptTypeItem.key : undefined}
                                            onChange={onPromptTypeChange}
                                            placeholder="Prompt Type"
                                            options={promptTypeOptions}
                                            disabled={false}
                                            styles={dropdownStyles}
                                    />
                                    <TextField
                                        className={styles.oneshotSettingsSeparator}
                                        value={promptTemplate}
                                        label="Override prompt template"
                                        multiline
                                        autoAdjustHeight
                                        onChange={onPromptTemplateChange}
                                    />
                                </div>
                                <ChoiceGroup
                                    className={styles.oneshotSettingsSeparator}
                                    label="Search Type"
                                    options={searchTypes}
                                    defaultSelectedKey={searchTypeOptions}
                                    onChange={onSearchTypeChange}
                                />
                                <SpinButton
                                    className={styles.chatSettingsSeparator}
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
                            </Panel>
                        </div>
                    </div>
                    </PivotItem>
                </Pivot>
            )}
        </div>
    );
};

export default VideoGpt;
