import { useRef, useState, useEffect, useMemo } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, Spinner, mergeStyles } from "@fluentui/react";
import { SparkleFilled } from "@fluentui/react-icons";

import { Dropdown, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';
import { Pivot, PivotItem } from '@fluentui/react';

import styles from "./ChatGpt.module.css";
import { Label } from '@fluentui/react/lib/Label';
import { ExampleList, ExampleModel } from "../../components/Example";

import { chatGptApi, chatGpt3Api, Approaches, AskResponse, ChatRequest, ChatTurn, refreshIndex, getSpeechApi, 
    getAllIndexSessions, getIndexSession, getIndexSessionDetail, deleteIndexSession, renameIndexSession } from "../../api";
import { Answer, AnswerError, AnswerLoading } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ClearChatButton } from "../../components/ClearChatButton";
import { SettingsButton } from "../../components/SettingsButton";
import { ChatSession } from "../../api/models";
import { DetailsList, DetailsListLayoutMode, SelectionMode, ConstrainMode, IDetailsListProps, 
    IDetailsRowStyles, DetailsRow, Selection, IObjectWithKey} from '@fluentui/react/lib/DetailsList';
import { SessionButton } from "../../components/SessionButton";
import { mergeStyleSets } from '@fluentui/react/lib/Styling';
import { MarqueeSelection } from '@fluentui/react/lib/MarqueeSelection';
import { Text } from "@fluentui/react";
import { Delete24Regular } from "@fluentui/react-icons";
import { RenameButton } from "../../components/RenameButton";

var audio = new Audio();

const ChatGpt = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(true);
    const [useAutoSpeakAnswers, setUseAutoSpeakAnswers] = useState<boolean>(false);

    const [options, setOptions] = useState<any>([])
    const [temperature, setTemperature] = useState<number>(0.3);
    const [tokenLength, setTokenLength] = useState<number>(500);

    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };

    const lastQuestionRef = useRef<string>("");
    const lastQuestionRef3 = useRef<string>("");
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    const [runningIndex, setRunningIndex] = useState<number>(-1);
    const [answers3, setAnswers3] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    
    const [chatSession, setChatSession] = useState<ChatSession | null>(null);
    const [sessionId, setSessionId] = useState<string>();
    const [sessionList, setSessionList] = useState<any[]>();

    const [exampleLoading, setExampleLoading] = useState(false)

    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; summary:string; qa:string;  }[]>();
    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [summary, setSummary] = useState<string>();
    const [qa, setQa] = useState<string>('');

    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const [selectedItems, setSelectedItems] = useState<any[]>([]);
    const [sessionName, setSessionName] = useState<string>('');

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

    const focusZoneProps = {
        className: classNames.focusZone,
        'data-is-scrollable': 'true',
    } as React.HTMLAttributes<HTMLElement>;
    
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
                    sessionId: currentSession.sessionId
                }
            };
            const result = await chatGptApi(request, String(selectedItem?.key), String(selectedIndex));
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

    const makeApiRequest3 = async (question: string) => {
        lastQuestionRef3.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const history: ChatTurn[] = answers3.map(a => ({ user: a[0], bot: a[1].answer }));
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
                    embeddingModelType: String(selectedEmbeddingItem?.key)
                }
            };
            const result = await chatGpt3Api(question, request, String(selectedItem?.key), String(selectedIndex));
            setAnswers3([...answers3, [question, result, null]]);
            if(useAutoSpeakAnswers){
                const speechUrl = await getSpeechApi(result.answer);
                setAnswers3([...answers3, [question, result, speechUrl]]);
                startOrStopSynthesis("gpt3", speechUrl, answers.length);
            }
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

    const deleteSession = async () => {
        const sessionName = String(selectedItems[0]?.['Session Name'])
        if (sessionName === 'No Sessions found' || sessionName === "undefined") {
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
        const oldSessionName = String(selectedItems[0]?.['Session Name'])
        if (oldSessionName === 'No Sessions found' || oldSessionName === "undefined") {
            alert("Select valid session to rename")
        }
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
    };

    const onSessionNameChange = (event: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        const oldSessionName = String(selectedItems[0]?.['Session Name'])
        if (newValue === undefined || newValue === "") {
            alert("Provide session name")
        }
        setSessionName(newValue || oldSessionName);
    };

    const clearChat3 = () => {
        lastQuestionRef3.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswers3([]);
    };

    const onEnableAutoSpeakAnswersChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseAutoSpeakAnswers(!!checked);
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onExampleClicked3 = (example: string) => {
        makeApiRequest3(example);
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
            if (answerType === 'gpt3') {
                answers3.map((answer, index) => {
                    speechAnswer = answer[1].answer
                })    
            } else if (answerType === 'gpt35') {
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
                    qa:blob.qa
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

                getCosmosSession(item?.key, item?.iType)

                const sampleQuestion = []
                const  questionList = item.qa.split("\\n")
                for (const item of questionList) {
                    if ((item != '')) {
                        sampleQuestion.push({
                            text: item.replace(/[0-9]./g, ''),
                            value: item.replace(/[0-9]./g, '')
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
        clearChat3();

        const defaultKey = item?.key
        let indexType = 'pinecone'

        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                indexType = item.iType
                setSelectedIndex(item.iType)
                setSummary(item.summary)
                setQa(item.qa)
                getCosmosSession(item?.key, item?.iType)

                const sampleQuestion = []

                const  questionList = item.qa.split("\\n")
                for (const item of questionList) {
                    if ((item != '')) {
                        sampleQuestion.push({
                            text: item.replace(/[0-9]./g, ''),
                            value: item.replace(/[0-9]./g, '')
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

    useEffect(() => {
        setOptions([])
        refreshBlob()
        setSelectedEmbeddingItem(embeddingOptions[0])
    }, [])

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [isLoading]);

    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "3"));
    };

    const onUseSemanticRankerChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticRanker(!!checked);
    };

    const onUseSemanticCaptionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticCaptions(!!checked);
    };

    const onExcludeCategoryChanged = (_ev?: React.FormEvent, newValue?: string) => {
        setExcludeCategory(newValue || "");
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
                        headerText="GPT3.5"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                        <div className={styles.commandsContainer}>
                            <ClearChatButton className={styles.commandButton} onClick={clearChat}  text="Clear chat" disabled={!lastQuestionRef.current || isLoading} />
                            <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            <div className={styles.commandButton}>{selectedItem ? 
                                "Document Name : "  + selectedItem.text : undefined}</div>
                        </div>
                        <div className={styles.commandsContainer}>
                            <SessionButton className={styles.commandButton} onClick={clearChat} />
                            <ClearChatButton className={styles.commandButton} onClick={deleteSession}  text="Delete Session" disabled={false} />
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
                                <TextField
                                    className={styles.chatSettingsSeparator}
                                    defaultValue={promptTemplate}
                                    label="Override prompt template"
                                    multiline
                                    autoAdjustHeight
                                    onChange={onPromptTemplateChange}
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
                    </PivotItem>
                    <PivotItem
                        headerText="GPT3"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                        <div className={styles.commandsContainer}>
                            <ClearChatButton className={styles.commandButton} onClick={clearChat3}  text="Clear chat" disabled={!lastQuestionRef3.current || isLoading} />
                            <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            <div className={styles.commandButton}>{selectedItem ? 
                                "Document Name : "  + selectedItem.text : undefined}</div>
                        </div>
                         <div className={styles.chatRoot}>
                            <div className={styles.chatContainer}>
                                {!lastQuestionRef3.current ? (
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
                                                onSend={question => makeApiRequest3(question)}
                                            />
                                        </div>
                                        {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                                        <ExampleList onExampleClicked={onExampleClicked3}
                                        EXAMPLES={
                                            exampleList
                                        } />
                                    </div>
                                ) : (
                                    <div className={styles.chatMessageStream}>
                                        {answers3.map((answer, index) => (
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
                                                        onSpeechSynthesisClicked={() => startOrStopSynthesis("gpt3", answer[2], index)}
                                                        onFollowupQuestionClicked={q => makeApiRequest3(q)}
                                                        showFollowupQuestions={useSuggestFollowupQuestions && answers3.length - 1 === index}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                        {isLoading && (
                                            <>
                                                <UserChatMessage message={lastQuestionRef3.current} />
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerLoading />
                                                </div>
                                            </>
                                        )}
                                        {error ? (
                                            <>
                                                <UserChatMessage message={lastQuestionRef3.current} />
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerError error={error.toString()} onRetry={() => makeApiRequest3(lastQuestionRef3.current)} />
                                                </div>
                                            </>
                                        ) : null}
                                        <div ref={chatMessageStreamEnd} />
                                        <div className={styles.chatInput}>
                                            <QuestionInput
                                                clearOnSend
                                                placeholder="Type a new question"
                                                disabled={isLoading}
                                                onSend={question => makeApiRequest3(question)}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>

                            {answers3.length > 0 && activeAnalysisPanelTab && (
                                <AnalysisPanel
                                    className={styles.chatAnalysisPanel}
                                    activeCitation={activeCitation}
                                    onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                                    citationHeight="810px"
                                    answer={answers3[selectedAnswer][1]}
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
                                <TextField
                                    className={styles.chatSettingsSeparator}
                                    defaultValue={promptTemplate}
                                    label="Override prompt template"
                                    multiline
                                    autoAdjustHeight
                                    onChange={onPromptTemplateChange}
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
                    </PivotItem>
              </Pivot>
            </div>
        </div>
    );
};

export default ChatGpt;
