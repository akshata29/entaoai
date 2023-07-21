import { useRef, useState, useEffect, useMemo } from "react";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, Stack, 
    IPivotItemProps, getFadedOverflowStyle, on} from "@fluentui/react";
import { ShieldLockRegular } from "@fluentui/react-icons";
import { SparkleFilled } from "@fluentui/react-icons";

import styles from "./Pib.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { AskResponse,  getPib, getUserInfo, Approaches } from "../../api";
import { pibChatGptApi, ChatRequest, ChatTurn, getAllIndexSessions, getIndexSession, getIndexSessionDetail, deleteIndexSession, renameIndexSession } from "../../api";
    
import { Label } from '@fluentui/react/lib/Label';
import { Pivot, PivotItem } from '@fluentui/react';
import { IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';
import { Amex } from "../../components/Symbols/Amex";
import { Nasdaq } from "../../components/Symbols/Nasdaq";
import { Nyse } from "../../components/Symbols/Nyse";
import { PrimaryButton } from "@fluentui/react";
import { type } from "microsoft-cognitiveservices-speech-sdk/distrib/lib/src/common.speech/RecognizerConfig";
import { ClearChatButton } from "../../components/ClearChatButton";
import { ChatSession } from "../../api/models";
import { SessionButton } from "../../components/SessionButton";
import { RenameButton } from "../../components/RenameButton";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { QuestionInput } from "../../components/QuestionInput";
import { UserChatMessage } from "../../components/UserChatMessage";
import { Answer, AnswerError, AnswerLoading } from "../../components/Answer";
import { MarqueeSelection } from '@fluentui/react/lib/MarqueeSelection';
import { DetailsList, DetailsListLayoutMode, SelectionMode, Selection} from '@fluentui/react/lib/DetailsList';


const Pib = () => {

    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 400 } };
    const dropdownShortStyles: Partial<IDropdownStyles> = { dropdown: { width: 150 } };

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [symbol, setSymbol] = useState<string>('AAPL');
    const [agentSummary, setAgentSummary] = useState<string>();
    const [taskAgentSummary, setTaskAgentSummary] = useState<string>();
    const [selectedExchange, setSelectedExchange] = useState<IDropdownOption>();
    const [selectedCompany, setSelectedCompany] = useState<IDropdownOption>();
    const [selectedCompanyOptions, setSelectedCompanyOptions] = useState<IDropdownOption>();
    const [showAuthMessage, setShowAuthMessage] = useState<boolean>(false);
    const [missingSymbol, setMissingSymbol] = useState<boolean>(false);
    const [biography, setBiography] = useState<any>();
    const [companyName, setCompanyName] = useState<string>();
    const [cik, setCik] = useState<string>();
    const [exchange, setExchange] = useState<string>();
    const [industry, setIndustry] = useState<string>();
    const [sector, setSector] = useState<string>();
    const [address, setAddress] = useState<string>();
    const [website, setWebsite] = useState<string>();
    const [description, setDescription] = useState<string>();
    const [latestTranscript, setLatestTranscript] = useState<string>();
    const [transcriptQuestions, setTranscriptQuestions] = useState<any>();
    const [pressReleases, setPressReleases] = useState<any>();
    const [secFilings, setSecFilings] = useState<any>();
    const [researchReport, setResearchReports] = useState<any>();

    const lastQuestionRef = useRef<string>("");
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);
    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    const [runningIndex, setRunningIndex] = useState<number>(-1);
    const [chatSession, setChatSession] = useState<ChatSession | null>(null);
    const [selectedItems, setSelectedItems] = useState<any[]>([]);
    const [sessionName, setSessionName] = useState<string>('');
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; summary:string; qa:string; chunkSize:string; chunkOverlap:string; promptType:string }[]>();
    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [sessionList, setSessionList] = useState<any[]>();
    const [oldSessionName, setOldSessionName] = useState<string>('');
    const [sessionId, setSessionId] = useState<string>();
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);
    const [selectedDoc, setSelectedDoc] = useState<IDropdownOption>();


    const exchangeOptions = [
        {
            key: 'AMEX',
            text: 'AMEX'
        },
        {
            key: 'NASDAQ',
            text: 'NASDAQ'
        },
        {
            key: 'NYSE',
            text: 'NYSE'
        }
    ]

    const docOptions = [
        {
            key: 'latestearningcalls',
            text: 'Earning Calls'
        },
        {
            key: 'latestsecfilings',
            text: 'SEC Filings'
        }
    ]

    const amexTickers =  Amex.Tickers.map((ticker) => {
        return {key: ticker.key, text: ticker.text}
    })

    const nasdaqTickers = Nasdaq.Tickers.map((ticker) => {
        return {key: ticker.key, text: ticker.text}
    })

    const nyseTickers = Nyse.Tickers.map((ticker) => {
        return {key: ticker.key, text: ticker.text}
    })

    const biographyColumns = [
        {
          key: 'Name',
          name: 'Name',
          fieldName: 'Name',
          minWidth: 200, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
          key: 'Title',
          name: 'Title',
          fieldName: 'Title',
          minWidth: 300, maxWidth: 300, isResizable: false, isMultiline: true
        },
        {
            key: 'Biography',
            name: 'Biography',
            fieldName: 'Biography',
            minWidth: 900, maxWidth: 1200, isResizable: false, isMultiline: true
        }
    ]

    const transcriptQuestionsColumns = [
        {
          key: 'Question',
          name: 'Question or Topic Summary',
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

    const pressReleasesColumns = [
        {
          key: 'releaseDate',
          name: 'Release Date',
          fieldName: 'releaseDate',
          minWidth: 100, maxWidth: 150, isResizable: false, isMultiline: true
        },
        {
          key: 'title',
          name: 'Press Release Title',
          fieldName: 'title',
          minWidth: 200, maxWidth: 300, isResizable: false, isMultiline: true
        },
        {
            key: 'summary',
            name: 'Press Release Summary',
            fieldName: 'summary',
            minWidth: 400, maxWidth: 500, isResizable: false, isMultiline: true
        },
        {
            key: 'sentiment',
            name: 'Sentiment',
            fieldName: 'sentiment',
            minWidth: 100, maxWidth: 150, isResizable: false, isMultiline: true
        },
        {
            key: 'sentimentScore',
            name: 'Sentiment Score',
            fieldName: 'sentimentScore',
            minWidth: 100, maxWidth: 150, isResizable: false, isMultiline: true
        }
    ]

    const secFilingsColumns = [
        {
          key: 'section',
          name: 'Sec Section',
          fieldName: 'section',
          minWidth: 100, maxWidth: 150, isResizable: false, isMultiline: true
        },
        {
          key: 'summaryType',
          name: 'Section Type',
          fieldName: 'summaryType',
          minWidth: 200, maxWidth: 300, isResizable: false, isMultiline: true
        },
        {
            key: 'summary',
            name: 'Section Summary',
            fieldName: 'summary',
            minWidth: 700, maxWidth: 900, isResizable: false, isMultiline: true
        }
    ]

    const researchReportColumns = [
        {
          key: 'key',
          name: 'Metrics',
          fieldName: 'key',
          minWidth: 200, maxWidth: 250, isResizable: false, isMultiline: true
        },
        {
          key: 'value',
          name: 'Recommendation or Score',
          fieldName: 'value',
          minWidth: 250, maxWidth: 300, isResizable: false, isMultiline: true
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
    
    const stackStyles: IStackStyles = {
        root: {
          // background: DefaultPalette.white,
          height: 450,
        },
    };

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

    // Tokens definition
    const outerStackTokens: IStackTokens = { childrenGap: 5 };
    const innerStackTokens: IStackTokens = {
        childrenGap: 5,
        padding: 10,
    };

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

    const onExchangeChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedExchange(item);
        if (item?.key === "AMEX") {
            setSelectedCompany(amexTickers[0]);
        } else if (item?.key === "NASDAQ") {
            setSelectedCompany(nasdaqTickers[0])
        } else if (item?.key === "NYSE") {
            setSelectedCompany(nyseTickers[0])
        }
    }

    const onDocChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedDoc(item);
        clearChat();
        getCosmosSession(String(item?.key), String(symbol))
    }

    const onCompanyChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSymbol(String(item?.key));
    };

    const onSymbolChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setSymbol(newValue || "");
        if (newValue == '') {
          setMissingSymbol(true)
        }
        else {
            setMissingSymbol(false)
        }
        getCosmosSession(String(selectedDoc?.key), String(newValue))
        clearChat();
    };

    const getUserInfoList = async () => {
        const userInfoList = await getUserInfo();
        if (userInfoList.length === 0 && window.location.hostname !== "localhost") {
            setShowAuthMessage(true);
        }
        else {
            setShowAuthMessage(false);
        }
    }

    const processPib = async (step: string) => {
        try {
            setIsLoading(true);
            await getPib(step, symbol, "azureopenai")
            .then(async (response) => {
                    const answer = JSON.parse(JSON.stringify(response.answer));
                    if (step == "1") {
                        setBiography(undefined)
                        setCompanyName(undefined)
                        setCik(undefined)
                        setExchange(undefined)
                        setIndustry(undefined)
                        setSector(undefined)
                        setWebsite(undefined)
                        setAddress(undefined)
                        setDescription(undefined)
                        setTranscriptQuestions(undefined)
                        setLatestTranscript(undefined)
                        setPressReleases(undefined)
                        setSecFilings(undefined);
                        setResearchReports(undefined);
                        for (let i = 0; i < answer.length; i++) {
                            if (answer[i].description == "Biography of Key Executives") {
                                const pibData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                const biographies = []
                                for (let i = 0; i < pibData.length; i++) 
                                {
                                    biographies.push({
                                        "Name": pibData[i]['name'],
                                        "Title": pibData[i]['title'],
                                        "Biography": pibData[i]['biography'],
                                        });
                                }
                                setBiography(biographies);
                            } else if (answer[i].description == "Company Profile")
                            {
                                const profileData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                setCompanyName(profileData[0]['companyName'])
                                setCik(profileData[0]['cik'])
                                setExchange(profileData[0]['exchange'])
                                setIndustry(profileData[0]['industry'])
                                setSector(profileData[0]['sector'])
                                setAddress(profileData[0]['address'] + " " + profileData[0]['city'] + " " + profileData[0]['state'] + " " + profileData[0]['zip'])
                                setWebsite(profileData[0]['website'])
                                setDescription(profileData[0]['description'])
                            }
                        }
                    } else if (step == "2") {
                        setTranscriptQuestions(undefined)
                        setLatestTranscript(undefined)
                        setPressReleases(undefined)
                        setSecFilings(undefined);
                        setResearchReports(undefined);
                        const dataPoints = response.data_points[0];
                        for (let i = 0; i < answer.length; i++) {
                            if (answer[i].description == "Earning Call Q&A") {
                                const pibData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                const tQuestions = []
                                for (let i = 0; i < pibData.length; i++) 
                                {
                                    tQuestions.push({
                                        "question": pibData[i]['question'],
                                        "answer": pibData[i]['answer'],
                                        });
                                }
                                setTranscriptQuestions(tQuestions);
                            }
                        }
                        setLatestTranscript(dataPoints)
                    } else if (step == "3") {
                        setPressReleases(undefined)
                        setSecFilings(undefined);
                        setResearchReports(undefined);
                        for (let i = 0; i < answer.length; i++) {
                            if (answer[i].description == "Press Releases") {
                                const pibData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                const pReleases = []
                                for (let i = 0; i < pibData.length; i++) 
                                {
                                    pReleases.push({
                                        "releaseDate": pibData[i]['releaseDate'],
                                        "title": pibData[i]['title'],
                                        "summary": pibData[i]['summary'],
                                        "sentiment": pibData[i]['sentiment'],
                                        "sentimentScore": pibData[i]['sentimentScore'],
                                        });
                                }
                                setPressReleases(pReleases);
                            }
                        }
                    } else if (step == "4") {
                        setSecFilings(undefined);
                        setResearchReports(undefined);
                        for (let i = 0; i < answer.length; i++) {
                            if (answer[i].description == "SEC Filings") {
                                const pibData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                const sFilings = []
                                for (let i = 0; i < pibData.length; i++) 
                                {
                                    sFilings.push({
                                        "section": pibData[i]['section'],
                                        "summaryType": pibData[i]['summaryType'],
                                        "summary": pibData[i]['summary'],
                                        });
                                }
                                setSecFilings(sFilings);
                            }
                        }
                    } else if (step == "5") {
                        setResearchReports(undefined);
                        for (let i = 0; i < answer.length; i++) {
                            if (answer[i].description == "Research Report") {
                                const pibData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                const rReports = []
                                for (let i = 0; i < pibData.length; i++) 
                                {
                                    rReports.push({
                                        "key": pibData[i]['key'],
                                        "value": pibData[i]['value'],
                                        });
                                }
                                setResearchReports(rReports);
                            }
                        }
                    }
                    else {
                        console.log("Step not defined")
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

    const deleteSession = async () => {
        //const sessionName = String(selectedItems[0]?.['Session Name'])
        if (sessionName === 'No Sessions found' || sessionName === "" || sessionName === undefined) {
            alert("Select Session to delete")
        }
        await deleteIndexSession(String(selectedDoc?.key), String(symbol), sessionName)
            .then(async (sessionResponse:any) => {
                getCosmosSession(String(selectedDoc?.key), String(symbol))
                clearChat();
        })

    };

    const renameSession = async () => {
        if (oldSessionName === 'No Sessions found' || oldSessionName === undefined || sessionName === "" || sessionName === undefined
        || oldSessionName === "" || sessionName === 'No Sessions found') {
            alert("Select valid session to rename")
        }
        else {
            await renameIndexSession(oldSessionName, sessionName)
                .then(async (sessionResponse:any) => {
                    getCosmosSession(String(selectedDoc?.key), String(symbol))
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

    const onSessionClicked = async (sessionFromList: any) => {
        //makeApiRequest(sessionFromList.name);
        const sessionName = sessionFromList["Session Name"]
        setSessionName(sessionName)
        setOldSessionName(sessionName)
        if (sessionName != "No Session Found") {
            try {
                await getIndexSession(String(selectedDoc?.key), String(symbol), sessionName)
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

    const generateQuickGuid = () => {
        return Math.random().toString(36).substring(2, 15) +
            Math.random().toString(36).substring(2, 15);
    }

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
          indexId: String(selectedDoc?.key),
          indexType: String(symbol),
          indexName: String(selectedDoc?.text),
          llmModel: 'gpt3.5',
          timestamp: String(new Date().getTime()),
          tokenUsed: 0,
          embeddingModelType: "azureopenai"
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
                    promptTemplate: '',
                    top: 3,
                    temperature: 0,
                    suggestFollowupQuestions: true,
                    tokenLength: 1000,
                    autoSpeakAnswers: false,
                    embeddingModelType: "azureopenai",
                    firstSession: firstSession,
                    session: JSON.stringify(currentSession),
                    sessionId: currentSession.sessionId,
                    deploymentType: "gpt3516k",
                    chainType: "stuff",
                }
            };
            const result = await pibChatGptApi(request, symbol, String(selectedDoc?.key));
            setAnswers([...answers, [question, result, null]]);
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const startOrStopSynthesis = async (answerType:string, url: string | null, index: number) => {
    };

    useEffect(() => {
        setSelectedExchange(exchangeOptions[0])
        setSelectedCompany(amexTickers[0]);

        setSelectedDoc(docOptions[0]);
        getCosmosSession(docOptions[0]?.key, String(symbol))
        if (window.location.hostname != "localhost") {
            getUserInfoList();
            setShowAuthMessage(true)
        } else
            setShowAuthMessage(false)
    }, [])

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [isLoading]);

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
            <div className={styles.oneshotContainer}>
            <Pivot aria-label="QA">
                    <PivotItem
                        headerText="Step 1"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                   <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <b>CoPilot</b> 
                                            <p>
                                            This use-case shows how to build your own CoPilot using the set of Cognitive Services on Microsoft Azure.  This use-case leverages the following services:
                                            <ul>
                                                <li>
                                                    <b>Bing Search</b> - This service is used to find the latest information on the company and the key executives.
                                                </li>
                                                <li>
                                                    <b>Azure OpenAI</b> - This service is used to generate content, summarize the content and answer questions.
                                                </li>
                                                <li>
                                                    <b>Speech Services</b> - This service is used to convert the speech to text.
                                                </li>
                                                <li>
                                                    <b>Cognitive Search</b> - This service is used as Vector store to persist the information.
                                                </li>
                                                <li>
                                                    <b>Azure Functions</b> - This service is to orchestrated the entire process.
                                                </li>
                                            </ul>
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 1 : </b> 
                                              This step focuses on extracting the company profile and the biography of the key executives. For this step
                                              we will be using the <b>Paid</b> API data services to extract the company profile for the company based on CIK.
                                              It will also find the key executives of the company. For the latest information on the biography, we will perform
                                              <b> Public</b> Internet search to find the latest information on the key executives and use GPT to summarize that information.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <Label>Exchange :</Label>
                                        &nbsp;
                                        <Dropdown
                                            selectedKey={selectedExchange?.key}
                                            onChange={onExchangeChange}
                                            placeholder="Select Exchange"
                                            options={exchangeOptions}
                                            disabled={false}
                                            styles={dropdownShortStyles}
                                            multiSelect={false}
                                        />
                                        {/* &nbsp;  
                                        <Label>Company :</Label>
                                        &nbsp;
                                        <Dropdown
                                            selectedKey={selectedCompany?.key}
                                            onChange={onCompanyChange}
                                            placeholder="Select Company"
                                            options={selectedExchange?.key == 'AMEX' ? amexTickers : selectedExchange?.key == 'NADSAQ' ? nasdaqTickers : nyseTickers}
                                            disabled={false}
                                            styles={dropdownStyles}
                                            multiSelect={false}
                                        /> */}
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} required={true} 
                                            errorMessage={!missingSymbol ? '' : "Symbol is required for PIB Functionality"}/>
                                        &nbsp;
                                        <PrimaryButton text="Process Step1" onClick={() => processPib("1")} disabled={isLoading} />
                                        <PrimaryButton text="ReProcess Step1" onClick={() => processPib("1")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                            <div>
                                                <br/>
                                                <Stack.Item grow={2} styles={stackItemStyles}>
                                                    <b>Company Name : </b> {companyName}
                                                    &nbsp;
                                                    <b>CIK : </b> {cik}
                                                </Stack.Item>
                                                <Stack.Item grow={2} styles={stackItemStyles}>
                                                    <b>Exchange : </b> {exchange}
                                                    &nbsp;
                                                    <b>Industry : </b> {industry}
                                                    &nbsp;
                                                    <b>Sector : </b> {sector}
                                                </Stack.Item>
                                                <Stack.Item grow={2} styles={stackItemStyles}>
                                                    <b>Address : </b> {address}
                                                    &nbsp;
                                                    <b>Website : </b> {website}
                                                </Stack.Item>
                                                <Stack.Item grow={2} styles={stackItemStyles}>
                                                    {description}
                                                </Stack.Item>
                                                <br/>
                                                <Stack enableScopedSelectors styles={stackItemCenterStyles} tokens={innerStackTokens}>
                                                    <Stack.Item grow={2} styles={stackItemCenterStyles}>
                                                        <DetailsList
                                                            compact={true}
                                                            items={biography || []}
                                                            columns={biographyColumns}
                                                            selectionMode={SelectionMode.none}
                                                            getKey={(item: any) => item.key}
                                                            selectionPreservedOnEmptyClick={true}
                                                            layoutMode={DetailsListLayoutMode.justified}
                                                            ariaLabelForSelectionColumn="Toggle selection"
                                                            checkButtonAriaLabel="select row"
                                                            />
                                                    </Stack.Item>
                                                </Stack>
                                        </div>
                                        )
                                    }
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Step 2"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 2 : </b> 
                                              This step focuses on extracting the earning call transcripts for the company for last 3 years. For this step
                                              we will be using the <b>Paid</b> API data services to extract the quarterly call transcripts.  There are options you can take to download the 
                                              transcript from the company's website as well.   Alternatively, you can take advantage of Cognitive Speech Service to generate transcript from
                                              the audio file that will be available <b>Publicly</b> on company's website.
                                              Once the transcript is acquired, we will use GPT to answer most common questions asked during the earning call as well as summarize
                                              the key information from the earning call.
                                              Following are the common questions asked during the earning call.
                                              <ul>
                                              <li>What are some of the current and looming threats to the business?</li>
                                              <li>What is the debt level or debt ratio of the company right now?</li>
                                              <li>How do you feel about the upcoming product launches or new products?</li>
                                              <li>How are you managing or investing in your human capital?</li>
                                              <li>How do you track the trends in your industry?</li>
                                              <li>Are there major slowdowns in the production of goods?</li>
                                              <li>How will you maintain or surpass this performance in the next few quarters?</li>
                                              <li>What will your market look like in five years as a result of using your product or service?</li>
                                              <li>How are you going to address the risks that will affect the long-term growth of the company?</li>
                                              <li>How is the performance this quarter going to affect the long-term goals of the company?</li>
                                              <li>Provide key information about revenue for the quarter</li>
                                              <li>Provide key information about profits and losses (P&L) for the quarter</li>
                                              <li>Provide key information about industry trends for the quarter</li>
                                              <li>Provide key information about business trends discussed on the call</li>
                                              <li>Provide key information about risk discussed on the call</li>
                                              <li>Provide key information about AI discussed on the call</li>
                                              <li>Provide any information about mergers and acquisitions (M&A) discussed on the call.</li>
                                              <li>Provide key information about guidance discussed on the call</li>
                                              </ul>
                                              Following is the summary we will generate.
                                              <ul>
                                                <li>Financial Results</li>
                                                <li>Business Highlights</li>
                                                <li>Future Outlook</li>
                                                <li>Business Risks</li>
                                                <li>Management Positive Sentiment</li>
                                                <li>Management Negative Sentiment</li>
                                                <li>Future Growth Strategies"</li>
                                              </ul>
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Process Step2" onClick={() => processPib("2")} />
                                        <PrimaryButton text="ReProcess Step2" onClick={() => processPib("2")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                        <div>
                                        <br/>
                                        <Stack enableScopedSelectors styles={stackItemCenterStyles} tokens={innerStackTokens}>
                                            <Stack.Item grow={2} styles={stackItemStyles}>
                                                <Label>Earning Call Transcript</Label>
                                                &nbsp; 
                                                <TextField onChange={onSymbolChange}  
                                                    value={latestTranscript} disabled={true}
                                                    style={{ resize: 'none', width: '1000px', height: '500px' }}
                                                    multiline/>
                                            </Stack.Item>
                                            <br/>
                                            <Stack.Item grow={2} styles={stackItemCenterStyles}>
                                                <DetailsList
                                                    compact={true}
                                                    items={transcriptQuestions || []}
                                                    columns={transcriptQuestionsColumns}
                                                    selectionMode={SelectionMode.none}
                                                    getKey={(item: any) => item.key}
                                                    selectionPreservedOnEmptyClick={true}
                                                    layoutMode={DetailsListLayoutMode.justified}
                                                    ariaLabelForSelectionColumn="Toggle selection"
                                                    checkButtonAriaLabel="select row"
                                                    />
                                            </Stack.Item>
                                        </Stack>
                                        </div>
                                    )}
                                </Stack>
                            </Stack>

                    </PivotItem>
                    <PivotItem
                        headerText="Step 3"
                        headerButtonProps={{
                        'data-order': 3,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 3 : </b> 
                                              This step focuses on accessing the <b>Publicly</b> available press releases for the company.  For our use-case we are focusing on
                                              generating summary only for the latest 25 press releases.  Besides genearting the summary, we are also using GPT to find 
                                              sentiment and the sentiment score for the press-releases.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Process Step3" onClick={() => processPib("3")} />
                                        <PrimaryButton text="ReProcess Step3" onClick={() => processPib("3")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                        <Stack enableScopedSelectors styles={stackItemCenterStyles} tokens={innerStackTokens}>
                                        <div>
                                        <br/>
                                            <Stack.Item grow={2} styles={stackItemCenterStyles}>
                                                <DetailsList
                                                    compact={true}
                                                    items={pressReleases || []}
                                                    columns={pressReleasesColumns}
                                                    selectionMode={SelectionMode.none}
                                                    getKey={(item: any) => item.key}
                                                    selectionPreservedOnEmptyClick={true}
                                                    layoutMode={DetailsListLayoutMode.justified}
                                                    ariaLabelForSelectionColumn="Toggle selection"
                                                    checkButtonAriaLabel="select row"
                                                    />
                                            </Stack.Item>
                                        </div>
                                        </Stack>
                                    )}
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Step 4"
                        headerButtonProps={{
                        'data-order': 4,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 4 : </b> 
                                              This step focuses on pulling the <b>Publicly</b> available 10-K annual filings for the company from the SEC Edgar website.
                                              Once the data is crawled, it is stored and persisted in the indexed Repository.  The data is then used to 
                                              generate the summary.   Summaries are generated for Item1, Item1A, Item3, Item5, Item7, Item7A and Item9 sections of the 10-K filing.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Process Step4" onClick={() => processPib("4")} />
                                        <PrimaryButton text="ReProcess Step4" onClick={() => processPib("4")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                            <div>
                                        <br/>
                                        <Stack enableScopedSelectors styles={stackItemCenterStyles} tokens={innerStackTokens}>
                                            <Stack.Item grow={2} styles={stackItemCenterStyles}>
                                                <DetailsList
                                                    compact={true}
                                                    items={secFilings || []}
                                                    columns={secFilingsColumns}
                                                    selectionMode={SelectionMode.none}
                                                    getKey={(item: any) => item.key}
                                                    selectionPreservedOnEmptyClick={true}
                                                    layoutMode={DetailsListLayoutMode.justified}
                                                    ariaLabelForSelectionColumn="Toggle selection"
                                                    checkButtonAriaLabel="select row"
                                                    />
                                            </Stack.Item>
                                        </Stack>
                                        </div>
                                    )}
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Step 5"
                        headerButtonProps={{
                        'data-order': 5,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 5 : </b> 
                                              This step focuses on pulling the <b>Private</b> data that generates the fundamental and technical scores for the company.
                                              It also shows the common analyst ratings and other information that is not publicly available.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Process Step5" onClick={() => processPib("5")} />
                                        <PrimaryButton text="ReProcess Step5" onClick={() => processPib("5")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                            <div>
                                        <br/>
                                        <Stack enableScopedSelectors styles={stackItemCenterStyles} tokens={innerStackTokens}>
                                            <Stack.Item grow={2} styles={stackItemCenterStyles}>
                                                <DetailsList
                                                    compact={true}
                                                    items={researchReport || []}
                                                    columns={researchReportColumns}
                                                    selectionMode={SelectionMode.none}
                                                    getKey={(item: any) => item.key}
                                                    selectionPreservedOnEmptyClick={true}
                                                    layoutMode={DetailsListLayoutMode.justified}
                                                    ariaLabelForSelectionColumn="Toggle selection"
                                                    checkButtonAriaLabel="select row"
                                                    />
                                            </Stack.Item>
                                        </Stack>
                                        </div>
                                    )}
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Chat Pib"
                        headerButtonProps={{
                        'data-order': 9,
                        }}
                    >
                        <div className={styles.root}>
                        <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <Label>Symbol :</Label>&nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        <Label>Talk to Document :</Label>&nbsp;
                                        <Dropdown
                                            selectedKey={selectedDoc ? selectedDoc.key : undefined}
                                            // eslint-disable-next-line react/jsx-no-bind
                                            onChange={onDocChange}
                                            placeholder="Select an PDF"
                                            options={docOptions}
                                            styles={dropdownStyles}
                                        />
                                    </Stack.Item>
                                </Stack>
                        </Stack>
                        <br/>
                        <div className={styles.commandsContainer}>
                            <ClearChatButton className={styles.commandButton} onClick={clearChat}  text="Clear chat" disabled={!lastQuestionRef.current || isLoading} />
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
                                        <h3 className={styles.chatEmptyStateTitle}>Chat with your Pitch Book</h3>
                                        <h4 className={styles.chatEmptyStateSubtitle}>Ask anything on {symbol} from {selectedDoc ? selectedDoc.text : ''}</h4>
                                        <div className={styles.chatInput}>
                                            <QuestionInput
                                                clearOnSend
                                                placeholder="Type a new question"
                                                disabled={isLoading}
                                                onSend={question => makeApiRequest(question)}
                                            />
                                        </div>
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
                                                        showFollowupQuestions={true}
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

                            {/* <div>
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
                            </div> */}
                        </div>
                    </div>

                    </PivotItem>
                </Pivot>
            </div>
            )}
        </div>
    );
};

export default Pib;

