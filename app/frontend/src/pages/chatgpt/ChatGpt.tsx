import { useRef, useState, useEffect, useMemo } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, Spinner, Stack, ChoiceGroup, IChoiceGroupOption } from "@fluentui/react";
import { SparkleFilled } from "@fluentui/react-icons";
import { ShieldLockRegular } from "@fluentui/react-icons";

import { Dropdown, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import styles from "./ChatGpt.module.css";
import { Label } from '@fluentui/react/lib/Label';
import { ExampleList, ExampleModel } from "../../components/Example";

import { chat, Approaches, AskResponse, ChatRequest, ChatTurn, refreshIndex, getSpeechApi, chatGpt, SearchTypes,
    getAllIndexSessions, getIndexSession, getIndexSessionDetail, deleteIndexSession, renameIndexSession, getUserInfo, chatStream } from "../../api";
import { Answer, AnswerError, AnswerLoading } from "../../components/Answer";
import { AnswerChat } from "../../components/Answer/AnswerChat";
import { QuestionInput } from "../../components/QuestionInput";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ClearChatButton } from "../../components/ClearChatButton";
import { SettingsButton } from "../../components/SettingsButton";
import { ChatSession } from "../../api/models";
import { DetailsList, DetailsListLayoutMode, SelectionMode, Selection} from '@fluentui/react/lib/DetailsList';
import { SessionButton } from "../../components/SessionButton";
import { mergeStyleSets } from '@fluentui/react/lib/Styling';
import { MarqueeSelection } from '@fluentui/react/lib/MarqueeSelection';
import { RenameButton } from "../../components/RenameButton";
import { Pivot, PivotItem } from '@fluentui/react';

var audio = new Audio();

const ChatGpt = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [isConfigPanelOpenGpt, setIsConfigPanelOpenGpt] = useState(false);
    const [isConfigPanelOpenStream, setIsConfigPanelOpenStream] = useState(false);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplateGpt, setPromptTemplateGpt] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(true);
    const [useAutoSpeakAnswers, setUseAutoSpeakAnswers] = useState<boolean>(false);
    const [searchTypeOptions, setSearchTypeOptions] = useState<SearchTypes>(SearchTypes.Similarity);

    const [options, setOptions] = useState<any>([])
    const [temperature, setTemperature] = useState<number>(0.3);
    const [tokenLength, setTokenLength] = useState<number>(500);
    const [temperatureGpt, setTemperatureGpt] = useState<number>(0.7);
    const [tokenLengthGpt, setTokenLengthGpt] = useState<number>(750);

    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };

    const lastQuestionRef = useRef<string>("");
    const lastQuestionRefGpt = useRef<string>("");
    const lastQuestionRefStream = useRef<string>("");
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    const [answerStream, setAnswersStream] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    const [runningIndex, setRunningIndex] = useState<number>(-1);
    const [answersGpt, setAnswersGpt] = useState<[user: string, response: string, speechUrl: string | null][]>([]);
    
    const [chatSession, setChatSession] = useState<ChatSession | null>(null);
    const [chatSessionGpt, setChatSessionGpt] = useState<ChatSession | null>(null);
    const [sessionId, setSessionId] = useState<string>();
    const [sessionIdGpt, setSessionIdGpt] = useState<string>();
    const [sessionList, setSessionList] = useState<any[]>();
    const [sessionListGpt, setSessionListGpt] = useState<any[]>();

    const [exampleLoading, setExampleLoading] = useState(false)

    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; summary:string; qa:string; chunkSize:string; chunkOverlap:string; promptType:string }[]>();
    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [summary, setSummary] = useState<string>();
    const [qa, setQa] = useState<string>('');

    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const [selectedEmbeddingItemGpt, setSelectedEmbeddingItemGpt] = useState<IDropdownOption>();
    const [selectedItems, setSelectedItems] = useState<any[]>([]);
    const [selectedItemsGpt, setSelectedItemsGpt] = useState<any[]>([]);
    const [sessionName, setSessionName] = useState<string>('');
    const [oldSessionName, setOldSessionName] = useState<string>('');
    const [sessionNameGpt, setSessionNameGpt] = useState<string>('');
    const [oldSessionNameGpt, setOldSessionNameGpt] = useState<string>('');
    const [showAuthMessage, setShowAuthMessage] = useState<boolean>(false);
    const [selectedDeploymentType, setSelectedDeploymentType] = useState<IDropdownOption>();
    const [selectedPromptTypeItem, setSelectedPromptTypeItem] = useState<IDropdownOption>();
    const [selectedDeploymentTypeGpt, setSelectedDeploymentTypeGpt] = useState<IDropdownOption>();
    const [selectedPromptTypeItemGpt, setSelectedPromptTypeItemGpt] = useState<IDropdownOption>();    
    const [selectedChunkSize, setSelectedChunkSize] = useState<string>()
    const [selectedChunkOverlap, setSelectedChunkOverlap] = useState<string>()
    const [selectedPromptType, setSelectedPromptType] = useState<string>()
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();
    const [chainTypeOptions, setChainTypeOptions] = useState<any>([])
    const [functionCall, setFunctionCall] = useState(false);

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
        controlWrapper: {
            display: 'flex',
            flexWrap: 'wrap',
        },
    });

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

    const promptTypeGptOptions = [
        {
          key: 'custom',
          text: 'custom'
        },
        {
          key: 'linuxTerminal',
          text: 'Linux Terminal'
        },
        {
          key: 'accountant',
          text: 'Accountant'
        },
        {
          key: 'realEstateAgent',
          text: 'Real Estate Agent'
        },
        {
            key: 'careerCounseler',
            text: 'Career Counseler'
        },
        {
            key: 'personalTrainer',
            text: 'Personal Trainer'
        }
    ]

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

    const selectionGpt = useMemo(
        () =>
        new Selection({
            onSelectionChanged: () => {
            setSelectedItemsGpt(selectionGpt.getSelection());
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
                    //isHeaderVisible={false}
                    //constrainMode={ConstrainMode.unconstrained}
                    onActiveItemChanged={(item:any) => onSessionClicked(item)}
                    //focusZoneProps={focusZoneProps}
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

    const detailsListChat = useMemo(
        () => (
            <MarqueeSelection selection={selectionGpt}>
                <DetailsList
                    className={styles.example}
                    items={sessionListGpt || []}
                    columns={sessionListColumn}
                    selectionMode={SelectionMode.single}
                    getKey={(item: any) => item.key}
                    setKey="single"
                    onActiveItemChanged={(item:any) => onSessionGptClicked(item)}
                    layoutMode={DetailsListLayoutMode.fixedColumns}
                    ariaLabelForSelectionColumn="Toggle selection"
                    checkButtonAriaLabel="select row"
                    selection={selectionGpt}
                    selectionPreservedOnEmptyClick={false}
                 />
             </MarqueeSelection>
         ),
         [selectionGpt, sessionListColumn, sessionListGpt]
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
    const makeApiStreamRequest = async (question: string) => {
        // let  currentSession = chatSession;
        // let firstSession = false;
        // if (!lastQuestionRef.current || currentSession === null) {
        //     currentSession = handleNewConversation();
        //     firstSession = true;
        //     let sessionLists = sessionList;
        //     sessionLists?.unshift({
        //         "Session Name": currentSession.sessionId,
        //     });
        //     setSessionList(sessionLists)
        // }
        lastQuestionRefStream.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const history: ChatTurn[] = answerStream.map(a => ({ user: a[0], bot: a[1].answer }));
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
                    //firstSession: firstSession,
                    //session: JSON.stringify(currentSession),
                    //sessionId: currentSession.sessionId,
                    deploymentType: String(selectedDeploymentType?.key),
                    chainType: String(selectedChain?.key),
                    searchType: searchTypeOptions,
                }
            };
            let result: any = {};
            let answer: string = '';
            let nextQuestion: string = '';
            const response = await chatStream(request,String(selectedItem?.key), String(selectedIndex));
            let askResponse: AskResponse = {} as AskResponse;
            if (response?.body) {
                const reader = response.body.getReader();
                let runningText = "";
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;

                    var text = new TextDecoder("utf-8").decode(value);
                    const objects = text.split("\n");
                    objects.forEach(async (obj) => {
                        try {
                            runningText += obj;
                            if (obj != "") {
                                result = JSON.parse(runningText)
                                if (result["data_points"]) {
                                    askResponse = result;
                                } else if (result["choices"] && result["choices"][0]["delta"]["content"]) {
                                    answer += result["choices"][0]["delta"]["content"];
                                    nextQuestion += answer.indexOf("NEXT QUESTIONS:") > -1 ? answer.substring(answer.indexOf('NEXT QUESTIONS:') + 15) : '';
                                    let latestResponse: AskResponse = {...askResponse, answer: answer, nextQuestions: nextQuestion};
                                    setIsLoading(false);
                                    setAnswersStream([...answerStream, [question, latestResponse, null]]);
                                    if(useAutoSpeakAnswers){
                                        const speechUrl = await getSpeechApi(result.answer);
                                        setAnswersStream([...answerStream, [question, latestResponse, speechUrl]]);
                                        startOrStopSynthesis("gpt35", speechUrl, answerStream.length);
                                    }
                                }
                            }
                            runningText = "";
                        }
                        catch { 
                            //console.log("Error parsing JSON: " + obj);
                        }
                    });
                }
            }
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };
    const makeApiRequestGpt = async (question: string) => {
        let  currentSession = chatSessionGpt;
        let firstSession = false;
        if (!lastQuestionRefGpt.current || currentSession === null) {
            currentSession = handleNewConversationGpt()
            firstSession = true;
            let sessionLists = sessionListGpt;
            sessionLists?.unshift({
                "Session Name": currentSession.sessionId,
            });
            setSessionListGpt(sessionLists)
        }
        let promptTemplate = "";
        if (firstSession) {
            if (selectedPromptTypeItemGpt?.key == "custom")
                setPromptTemplateGpt(question);

            promptTemplate = question;
        }
        else {
            //promptTemplate = promptTemplateGpt;
            promptTemplate = answersGpt[0][0];
        }
        lastQuestionRefGpt.current = question;

        error && setError(undefined);
        setIsLoading(true);

        try {
            const history: ChatTurn[] = answersGpt.map(a => ({ user: a[0], bot: a[1] }));
            const request: ChatRequest = {
                history: [...history, { user: question, bot: undefined }],
                approach: Approaches.ReadRetrieveRead,
                overrides: {
                    promptTemplate: promptTemplate,
                    temperature: temperatureGpt,
                    tokenLength: tokenLengthGpt,
                    embeddingModelType: String(selectedEmbeddingItemGpt?.key),
                    firstSession: firstSession,
                    session: JSON.stringify(currentSession),
                    sessionId: currentSession.sessionId,
                    deploymentType: String(selectedDeploymentTypeGpt?.key),
                    functionCall:functionCall,
                    searchType: searchTypeOptions,
                }
            };
            const result = await chatGpt(request, 'chatgpt', 'cogsearchvs');
            setAnswersGpt([...answersGpt, [question, result.answer, null]]);
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
                if (indexNs == "chatgpt") {
                    setSessionListGpt(sessionLists)
                } else {
                    setSessionList(sessionLists)
                }
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
        setSelectedItems([])
        setSessionName('');
    };

    const clearStreamChat = () => {
        lastQuestionRefStream.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswersStream([]);
        setSelectedItems([])
    };

    const clearChatGpt = () => {
        lastQuestionRefGpt.current = "";
        error && setError(undefined);
        setChatSessionGpt(null)
        setAnswersGpt([]);
        setSelectedItemsGpt([])
        setSessionNameGpt('');
        setSelectedPromptTypeItemGpt(promptTypeGptOptions[0])
        setPromptTemplateGpt('')
    };
    const deleteSession = async () => {
        //const sessionName = String(selectedItems[0]?.['Session Name'])
        if (sessionName === 'No Sessions found' || sessionName === "" || sessionName === undefined) {
            alert("Select Session to delete")
        }
        await deleteIndexSession(String(selectedItem?.key), String(selectedIndex), sessionName)
            .then(async (sessionResponse:any) => {
                const defaultKey = selectedItem?.key
                indexMapping?.findIndex((item) => {
                    if (item.key == defaultKey) {
                        getCosmosSession(item?.key, item?.iType)
                    }
                })
                clearChat();
        })

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

    const deleteSessionGpt = async () => {
        if (sessionNameGpt === 'No Sessions found' || sessionNameGpt === "" || sessionNameGpt === undefined) {
            alert("Select Session to delete")
        }
        await deleteIndexSession("chatgpt", "cogsearchvs", sessionNameGpt)
            .then(async (sessionResponse:any) => {
                getCosmosSession("chatgpt", "cogsearchvs")
                clearChatGpt();
        })

    };
    const renameSessionGpt = async () => {
        if (oldSessionNameGpt === 'No Sessions found' || oldSessionNameGpt === undefined || sessionNameGpt === "" || sessionNameGpt === undefined
        || oldSessionNameGpt === "" || oldSessionNameGpt === 'No Sessions found') {
            alert("Select valid session to rename")
        }
        else {
            await renameIndexSession(oldSessionNameGpt, sessionNameGpt)
                .then(async (sessionResponse:any) => {
                    getCosmosSession("chatgpt", "cogsearchvs")
                    clearChatGpt();
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

    const onSessionNameChangeGpt = (event: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        const oldSessionNameGpt = String(selectedItemsGpt[0]?.['Session Name'])
        if (newValue === undefined || newValue === "") {
            alert("Provide session name")
        }
        setSessionNameGpt(newValue || oldSessionNameGpt);
    };

    const onEnableAutoSpeakAnswersChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseAutoSpeakAnswers(!!checked);
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onExampleStreamClicked = (example: string) => {
        makeApiStreamRequest(example);
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
                    qa:blob.qa,
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
                setSummary(item.summary)
                setQa(item.qa)
                setSelectedChunkOverlap(item.chunkOverlap)
                setSelectedChunkSize(item.chunkSize)
                setSelectedPromptType(item.promptType)
                setSelectedPromptTypeItem(promptTypeOptions.find(x => x.key === item.promptType))
                updatePrompt(item.promptType)

                if (Number(item.chunkSize) > 4000) {
                    setSelectedDeploymentType(deploymentTypeOptions[1])
                } else {
                    setSelectedDeploymentType(deploymentTypeOptions[0])
                }

                getCosmosSession(item?.key, item?.iType)

                const sampleQuestion = []
                const  questionList = item.qa.split("\\n")
                for (const item of questionList) {
                    if ((item != '')) {
                        sampleQuestion.push({
                            text: item.replace(/^\d+\.\s*/, '').replace('<', '').replace('>', ''),
                            value: item.replace(/^\d+\.\s*/, '').replace('<', '').replace('>', '')
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

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedItem(item);
        clearChat();
        clearStreamChat();

        const defaultKey = item?.key
        let indexType = 'pinecone'

        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                indexType = item.iType
                setSelectedIndex(item.iType)
                setSummary(item.summary)
                setQa(item.qa)
                setSelectedChunkSize(item.chunkSize)
                setSelectedChunkOverlap(item.chunkOverlap)
                setSelectedPromptType(item.promptType)
                setSelectedPromptTypeItem(promptTypeOptions.find(x => x.key === item.promptType))
                updatePrompt(item.promptType)

                if (Number(item.chunkSize) > 4000) {
                    setSelectedDeploymentType(deploymentTypeOptions[1])
                } else {
                    setSelectedDeploymentType(deploymentTypeOptions[0])
                }

                getCosmosSession(item?.key, item?.iType)

                const sampleQuestion = []

                const  questionList = item.qa.split("\\n")
                for (const item of questionList) {
                    if ((item != '')) {
                        sampleQuestion.push({
                            text: item.replace(/^\d+\.\s*/, '').replace('<', '').replace('>', ''),
                            value: item.replace(/^\d+\.\s*/, '').replace('<', '').replace('>', '')
                        })
                    } 
                }
                const generatedExamples: ExampleModel[] = sampleQuestion
                setExampleList(generatedExamples)
                setExampleLoading(false)
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

    const onSessionGptClicked = async (sessionFromList: any) => {
        //makeApiRequest(sessionFromList.name);
        const sessionName = sessionFromList["Session Name"]
        setSessionNameGpt(sessionName)
        setOldSessionNameGpt(sessionName)
        if (sessionName != "No Session Found") {
            try {
                await getIndexSession("chatgpt", "cogsearchvs", sessionName)
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
                    setChatSessionGpt(newSession);
                    await getIndexSessionDetail(sessionId)
                    .then(async (response:any) => {
                        const rows = response.reduce(function (rows: any[][], key: any, index: number) { 
                            return (index % 2 == 0 ? rows.push([key]) 
                            : rows[rows.length-1].push(key)) && rows;
                        }, []);
                        const sessionLists: [string, string, string | null][] = [];
                        for (const session of rows)
                        {
                            sessionLists.push([session[0].content, session[1].content, null]);
                        }
                        lastQuestionRefGpt.current = sessionLists[sessionLists.length - 1][0];
                        setAnswersGpt(sessionLists);
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

    const updatePromptGpt = (promptType: string) => {       
        const linuxTerminal = `i want you to act as a linux terminal. I will type commands and you will reply with 
        what the terminal should show. I want you to only reply with the terminal output inside one unique code block, 
        and nothing else. do not write explanations. do not type commands unless I instruct you to do so. 
        when i need to tell you something in english, i will do so by putting text inside curly brackets {like this}. 
        my first command is pwd
        `

        const accountant = `I want you to act as an accountant and come up with creative ways to manage finances. 
        You'll need to consider budgeting, investment strategies and risk management when creating a financial plan 
        for your client. In some cases, you may also need to provide advice on taxation laws and regulations in 
        order to help them maximize their profits. 
        My first suggestion request is "Create a financial plan for a small business that focuses on cost savings and long-term investments".
        `

        const realEstateAgent = `I want you to act as a real estate agent. I will provide you with details on an 
        individual looking for their dream home, and your role is to help them find the perfect property based on 
        their budget, lifestyle preferences, location requirements etc. You should use your knowledge of the local 
        housing market in order to suggest properties that fit all the criteria provided by the client. 
        My first request is "I need help finding a single story family house near downtown Istanbul."
        `

        const careerCounseler = `I want you to act as a career counselor. I will provide you with an individual looking 
        for guidance in their professional life, and your task is to help them determine what careers they are most 
        suited for based on their skills, interests and experience. You should also conduct research into the various 
        options available, explain the job market trends in different industries and advice on which qualifications
        would be beneficial for pursuing particular fields. 
        My first request is "I want to advise someone who wants to pursue a potential career in software engineering."
        `
        
        const personalTrainer = `I want you to act as a personal trainer. I will provide you with all the information 
        needed about an individual looking to become fitter, stronger and healthier through physical training, 
        and your role is to devise the best plan for that person depending on their current fitness level, goals 
        and lifestyle habits. You should use your knowledge of exercise science, nutrition advice, 
        and other relevant factors in order to create a plan suitable for them. 
        My first request is “I need help designing an exercise program for someone who wants to lose weight.”
        `
        if (promptType == "linuxTerminal") {
            setPromptTemplateGpt(linuxTerminal)
            makeApiRequestGpt(linuxTerminal)
        }
        else if (promptType == "accountant") {
            setPromptTemplateGpt(accountant)
            makeApiRequestGpt(accountant)
        } else if (promptType == "realEstateAgent") {
            setPromptTemplateGpt(realEstateAgent)
            makeApiRequestGpt(realEstateAgent)
        } else if (promptType == "careerCounseler") {
            setPromptTemplateGpt(careerCounseler)
            makeApiRequestGpt(careerCounseler)
        } else if (promptType == "personalTrainer") {
            setPromptTemplateGpt(personalTrainer)
            makeApiRequestGpt(personalTrainer)
        } else if (promptType == "custom") {
            setPromptTemplateGpt("")
        }
    }
    
    useEffect(() => {
        if (window.location.hostname != "localhost") {
            getUserInfoList();
            setShowAuthMessage(true)
        } else
            setShowAuthMessage(false)

        setOptions([])
        refreshBlob()
        setChainTypeOptions(chainType)
        setSelectedChain(chainType[0])
        setSelectedEmbeddingItem(embeddingOptions[0])
        setSelectedDeploymentType(deploymentTypeOptions[0])
        setSelectedEmbeddingItemGpt(embeddingOptions[0])
        setSelectedDeploymentTypeGpt(deploymentTypeOptions[0])
        setSelectedPromptTypeItem(promptTypeOptions[0])
        setSelectedPromptTypeItemGpt(promptTypeGptOptions[0])
    }, [])

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [isLoading]);

    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
    };

    const onPromptTemplateChangeGpt = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplateGpt(newValue || "");
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

    const onTemperatureChangeGpt = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTemperatureGpt(parseInt(newValue || "0.3"));
    };

    const onTokenLengthChangeGpt = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTokenLengthGpt(parseInt(newValue || "500"));
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItem(item);
    };
    
    const onEmbeddingChangeGpt = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItemGpt(item);
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

    const handleNewConversationGpt = () => {
        const sessId = generateQuickGuid(); //uuidv4();
        setSessionIdGpt(sessId);

        const newSession: ChatSession = {
          id: generateQuickGuid(),
          type: 'Session',
          sessionId: sessId,
          name: sessId,
          chainType: 'stuff',
          feature: 'chat',
          indexId: "chatgpt",
          indexType: "cogsearchvs",
          indexName: "Chat GPT",
          llmModel: 'gpt3.5',
          timestamp: String(new Date().getTime()),
          tokenUsed: 0,
          embeddingModelType: String(selectedEmbeddingItemGpt?.key)
        };
        setChatSessionGpt(newSession);
        return newSession;
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

    const onDeploymentTypeChangeGpt = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedDeploymentTypeGpt(item);
    };

    const onPromptTypeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedPromptTypeItem(item);
        updatePrompt(String(item?.key));
    };

    const onPromptTypeChangeGpt = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        clearChatGpt()
        setSelectedPromptTypeItemGpt(item);
        updatePromptGpt(String(item?.key));
    };

    const onFunctionCallChanged = (ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean): void => {
        setFunctionCall(!!checked);
    };

    const onTabChange = (item?: PivotItem | undefined, ev?: React.MouseEvent<HTMLElement, MouseEvent> | undefined): void => {
        if (item?.props.headerText === "Chat On Data") {
            getCosmosSession(String(selectedItem?.key), String(selectedIndex))
        } 
        if (item?.props.headerText === "Chat Gpt") {
            getCosmosSession("chatgpt", "cogsearchvs")
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
                        headerText="Chat On Data"
                        headerButtonProps={{
                        'data-order': 1,
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
                                    <DefaultButton onClick={refreshBlob}>Refresh Docs</DefaultButton>
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
                    <PivotItem
                        headerText="Chat on Data - Stream"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                    <div className={styles.root}>
                        <br/>
                        <div className={styles.commandsContainer}>
                            <ClearChatButton className={styles.commandButton} onClick={clearStreamChat}  text="Clear chat" disabled={!lastQuestionRefStream.current || isLoading} />
                            <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpenStream(!isConfigPanelOpenStream)} />
                            <div className={styles.commandButton}>{selectedItem ? 
                                "Document Name : "  + selectedItem.text : undefined}</div>
                        </div>
                        <div className={styles.chatRoot}>
                            <div className={styles.chatContainer}>
                                {!lastQuestionRefStream.current ? (
                                    <div className={styles.chatEmptyState}>
                                        <SparkleFilled fontSize={"30px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" />
                                        <h3 className={styles.chatEmptyStateTitle}>Chat with your data - Stream</h3>
                                        <div className={styles.example}>
                                            <p className={styles.exampleText}><b>Document Summary</b> : {summary}</p>
                                        </div>
                                        <h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>
                                        <div className={styles.chatInput}>
                                            <QuestionInput
                                                clearOnSend
                                                placeholder="Type a new question"
                                                disabled={isLoading}
                                                onSend={question => makeApiStreamRequest(question)}
                                            />
                                        </div>
                                        {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                                        <ExampleList onExampleClicked={onExampleStreamClicked}
                                        EXAMPLES={
                                            exampleList
                                        } />
                                    </div>
                                ) : (
                                    <div className={styles.chatMessageStream}>
                                        {answerStream.map((answer, index) => (
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
                                                        onFollowupQuestionClicked={q => makeApiStreamRequest(q)}
                                                        onSpeechSynthesisClicked={() => startOrStopSynthesis("gpt35", answer[2], index)}
                                                        showFollowupQuestions={useSuggestFollowupQuestions && answers.length - 1 === index}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                        {isLoading && (
                                            <>
                                                <UserChatMessage message={lastQuestionRefStream.current} />
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerLoading />
                                                </div>
                                            </>
                                        )}
                                        {error ? (
                                            <>
                                                <UserChatMessage message={lastQuestionRefStream.current} />
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerError error={error.toString()} onRetry={() => makeApiStreamRequest(lastQuestionRefStream.current)} />
                                                </div>
                                            </>
                                        ) : null}
                                        <div ref={chatMessageStreamEnd} />
                                        <div className={styles.chatInput}>
                                            <QuestionInput
                                                clearOnSend
                                                placeholder="Type a new question"
                                                disabled={isLoading}
                                                onSend={question => makeApiStreamRequest(question)}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {answerStream.length > 0 && activeAnalysisPanelTab && (
                                <AnalysisPanel
                                    className={styles.chatAnalysisPanel}
                                    activeCitation={activeCitation}
                                    onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                                    citationHeight="810px"
                                    answer={answerStream[selectedAnswer][1]}
                                    activeTab={activeAnalysisPanelTab}
                                />
                            )}

                            <Panel
                                headerText="Configure Chat Interaction"
                                isOpen={isConfigPanelOpenStream}
                                isBlocking={false}
                                onDismiss={() => setIsConfigPanelOpenStream(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpenStream(false)}>Close</DefaultButton>}
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
                    <PivotItem
                        headerText="Chat Gpt"
                        headerButtonProps={{
                        'data-order': 3,
                        }}
                    >
                        <div className={styles.root}>
                            <br/>
                            <div className={styles.commandsContainer}>
                                <ClearChatButton className={styles.commandButton} onClick={clearChatGpt}  text="Clear chat" disabled={!lastQuestionRefGpt.current || isLoading} />
                                <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpenGpt(!isConfigPanelOpenGpt)} />
                                <Checkbox label="Function Call" checked={functionCall} onChange={onFunctionCallChanged} />
                            </div>
                            <div className={styles.commandsContainer}>
                                <SessionButton className={styles.commandButton} onClick={clearChatGpt} />
                                {/* <ClearChatButton className={styles.commandButton} onClick={deleteSessionGpt}  text="Delete Session" disabled={false} /> */}
                                <RenameButton className={styles.commandButton}  onClick={renameSessionGpt}  text="Rename Session"/>
                                <TextField className={styles.commandButton} value={sessionNameGpt} onChange={onSessionNameChangeGpt}
                                    styles={{root: {width: '200px'}}} />
                            </div>
                            {/* <div className={styles.chatRoot}> */}
                            <Stack horizontal className={styles.chatRoot}>
                                {detailsListChat}
                                <div className={styles.chatContainer}>
                                    {!lastQuestionRefGpt.current ? (
                                        <Stack className={styles.chatEmptyState}>
                                            <h1 className={styles.chatEmptyStateTitle}>Start chatting</h1>
                                            <h2 className={styles.chatEmptyStateSubtitle}>This chatbot is configured to answer your questions</h2>
                                            <div className={styles.chatInput}>
                                                <QuestionInput
                                                    clearOnSend
                                                    placeholder="Type a new question"
                                                    disabled={isLoading}
                                                    onSend={question => makeApiRequestGpt(question)}
                                                />
                                            </div>
                                        </Stack>
                                    ) : (
                                        <div className={styles.chatMessageStream} style={{ marginBottom: isLoading ? "40px" : "0px"}} role="log">
                                            {answersGpt.map((answer, index) => (
                                                <div key={index}>
                                                    <UserChatMessage message={answer[0]} />
                                                    <div className={styles.chatMessageGpt}>
                                                        <AnswerChat
                                                            key={index}
                                                            answer={answer[1]}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                            {isLoading && (
                                                <>
                                                    <UserChatMessage message={lastQuestionRefGpt.current} />
                                                    <div className={styles.chatMessageGptMinWidth}>
                                                        <AnswerLoading />
                                                    </div>
                                                </>
                                            )}
                                            {error ? (
                                                <>
                                                    <UserChatMessage message={lastQuestionRefGpt.current} />
                                                    <div className={styles.chatMessageGptMinWidth}>
                                                        <AnswerError error={error.toString()} onRetry={() => makeApiRequestGpt(lastQuestionRefGpt.current)} />
                                                    </div>
                                                </>
                                            ) : null}
                                            <div ref={chatMessageStreamEnd} />
                                            <div className={styles.chatInput}>
                                                <QuestionInput
                                                    clearOnSend
                                                    placeholder="Type a new question"
                                                    disabled={isLoading}
                                                    onSend={question => makeApiRequestGpt(question)}
                                                />
                                            </div>
                                        </div>
                                    )}
                                </div>
                                </Stack>
                            {/* </div> */}

                            <Panel
                                headerText="Configure Chat Interaction"
                                isOpen={isConfigPanelOpenGpt}
                                isBlocking={false}
                                onDismiss={() => setIsConfigPanelOpenGpt(false)}
                                closeButtonAriaLabel="Close"
                                onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpenGpt(false)}>Close</DefaultButton>}
                                isFooterAtBottom={true}
                            >
                                <br/>
                                <div>
                                    <Label>LLM Model</Label>
                                    <Dropdown
                                        selectedKey={selectedEmbeddingItemGpt ? selectedEmbeddingItemGpt.key : undefined}
                                        onChange={onEmbeddingChangeGpt}
                                        placeholder="Select an LLM Model"
                                        options={embeddingOptions}
                                        disabled={false}
                                        styles={dropdownStyles}
                                    />
                                </div>
                                <div>
                                    <Label>Deployment Type</Label>
                                    <Dropdown
                                            selectedKey={selectedDeploymentTypeGpt ? selectedDeploymentTypeGpt.key : undefined}
                                            onChange={onDeploymentTypeChangeGpt}
                                            placeholder="Select an Deployment Type"
                                            options={deploymentTypeOptions}
                                            disabled={((selectedEmbeddingItemGpt?.key == "openai" ? true : false) || (Number(selectedChunkSize) > 4000 ? true : false))}
                                            styles={dropdownStyles}
                                    />
                                </div>
                                <div>
                                    <Label>Prompt Type</Label>
                                    <Dropdown
                                            selectedKey={selectedPromptTypeItemGpt ? selectedPromptTypeItemGpt.key : undefined}
                                            onChange={onPromptTypeChangeGpt}
                                            placeholder="Prompt Type"
                                            options={promptTypeGptOptions}
                                            disabled={false}
                                            styles={dropdownStyles}
                                    />
                                    <TextField
                                        className={styles.oneshotSettingsSeparator}
                                        value={promptTemplateGpt}
                                        label="Override prompt template"
                                        multiline
                                        autoAdjustHeight
                                        onChange={onPromptTemplateChangeGpt}
                                    />
                                </div>
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Set the Temperature:"
                                    min={0.0}
                                    max={1.0}
                                    defaultValue={temperatureGpt.toString()}
                                    onChange={onTemperatureChangeGpt}
                                />
                                <SpinButton
                                    className={styles.oneshotSettingsSeparator}
                                    label="Max Length (Tokens):"
                                    min={0}
                                    max={4000}
                                    defaultValue={tokenLengthGpt.toString()}
                                    onChange={onTokenLengthChangeGpt}
                                />
                            </Panel>
                        </div>
                    </PivotItem>
                </Pivot>
            )}
        </div>
    );
};

export default ChatGpt;
