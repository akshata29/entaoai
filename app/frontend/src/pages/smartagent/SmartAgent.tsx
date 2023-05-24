import { useRef, useState, useEffect } from "react";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, Stack, IPivotItemProps, getFadedOverflowStyle} from "@fluentui/react";

import styles from "./SmartAgent.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { smartAgent, Approaches, AskResponse, AskRequest, getSpeechApi } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { Label } from '@fluentui/react/lib/Label';
import { ExampleList, ExampleModel } from "../../components/Example";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";
import { ClearChatButton } from "../../components/ClearChatButton";
import { Pivot, PivotItem } from '@fluentui/react';
import { IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';

var audio = new Audio();

const SmartAgent = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [approach, setApproach] = useState<Approaches>(Approaches.RetrieveThenRead);
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [temperature, setTemperature] = useState<number>(0);
    const [tokenLength, setTokenLength] = useState<number>(1000);
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(true);
    const [useAutoSpeakAnswers, setUseAutoSpeakAnswers] = useState<boolean>(false);
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };

    const lastAgentQuestionRef = useRef<string>("");

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [errorAgent, setAgentError] = useState<unknown>();
    const [answerAgent, setAgentAnswer] = useState<[AskResponse, string | null]>();


    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();

    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [agentSummary, setAgentSummary] = useState<string>();
    const [chainTypeOptions, setChainTypeOptions] = useState<any>([])

    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();

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
                    top: retrieveCount,
                    temperature: temperature,
                    chainType: String(selectedChain?.key),
                    tokenLength: tokenLength,
                    suggestFollowupQuestions: useSuggestFollowupQuestions,
                    autoSpeakAnswers: useAutoSpeakAnswers,
                    embeddingModelType: String(selectedEmbeddingItem?.key)
                }
            };
            const result = await smartAgent(request);
            setAgentAnswer([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setAgentAnswer([result, speechUrl]);
                startSynthesis("SmartAgent", speechUrl);
            }
        } catch (e) {
            setAgentError(e);
        } finally {
            setIsLoading(false);
        }
    };


    const approaches: IChoiceGroupOption[] = [
        {
            key: Approaches.RetrieveThenRead,
            text: "Retrieve-Then-Read"
        }
    ];

    const startSynthesis = async (answerType: string, url: string | null) => {
        if(isSpeaking) {
            audio.pause();
            setIsSpeaking(false);
        }

        if(url === null) {
            let speechAnswer;
            speechAnswer = answerAgent && answerAgent[0].answer;
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

    const onUseSuggestFollowupQuestionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSuggestFollowupQuestions(!!checked);
    };

    const onTemperatureChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTemperature(parseInt(newValue || "0.3"));
    };

    const onTokenLengthChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTokenLength(parseInt(newValue || "1000"));
    };

    const onExampleClicked = (example: string) => {
        makeApiAgentRequest(example);
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


    const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedChain(item);
    };

    const documentSummaryAndQa = async () => {
        const sampleQuestion = []
        const  questionList = [] 
        questionList.push("Should I create one or multiple Purview accounts and why?")
        questionList.push("Which shippers can ship the orders?")
        questionList.push("What is the difference between Serverless and Dedicated Pool")
        questionList.push("How many customers did placed an order")
        questionList.push("For the year 1996 give me subtotals for each order")
        questionList.push("What is context learning and three type of the approach?")
        questionList.push("How many orders were placed in 1998")
        questionList.push("What are the best practices to write secure code?")
        questionList.push("How does copy data tool work in Azure Synapse?")
        questionList.push("How can developers prevent evil input?")
        questionList.push("What are the features of ChatGPT + Enterprise Data")
        questionList.push("What vectorstore are supported by ChatGPT + Enterprise Data?")
        questionList.push("What are the list of the features and updates released in ChatGPT + Enterprise Data?")
        questionList.push("List of the Products that are above average price, also show average price for each product")
        questionList.push("What is the purpose of integrate hub in Synapse")
        questionList.push("How is the weather in Chicago tomorrow?")
        questionList.push("Give me rundown on top news for today")
        questionList.push("What are the top stories in the world today?")
        questionList.push("Which stocks are the movers and shakers today?")

        const shuffled = questionList.sort(() => 0.5 - Math.random());
        const selectedQuestion = shuffled.slice(0, 5);

        for (const item of selectedQuestion) {
            if ((item != '')) {
                sampleQuestion.push({
                    text: item,
                    value: item,
                })
            } 
        }
        const generatedExamples: ExampleModel[] = sampleQuestion
        setExampleList(generatedExamples)

        setAgentSummary("This sample shows how we can build Agents that uses set of tools and then get the answer.  The goal is that regardless of the information that we" +
        " have stored here (Cognitive Search, Cognitive Search Vector Store, Pinecone, Redis or any other document store) or processing the data" + 
        " that is in CSV format (and using CSV Agent or Pandas Agent) or retrieving information from Database (SQL Agent), the Agent can" +
        " answer the question correctly using the right tool.  Beyond the data that is stored in here, the Agent can also use the tool" + 
        " to find the current event and information from the web (using Bing Search Agent) and then answer the question.")
    }

    useEffect(() => {
        setChainTypeOptions(chainType)
        setSelectedChain(chainType[0])
        setSelectedEmbeddingItem(embeddingOptions[0])
        documentSummaryAndQa()

    }, [])

    const clearAgentChat = () => {
        lastAgentQuestionRef.current = "";
        errorAgent && setAgentError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAgentAnswer(undefined);
    };

    return (

        <div className={styles.root}>
            <div className={styles.oneshotContainer}>
            <Pivot aria-label="QA">
                    <PivotItem
                        headerText="Smart Agent"
                        headerButtonProps={{
                        'data-order': 2,
                        }}>
                        <div className={styles.oneshotTopSection}>
                            <div className={styles.commandsContainer}>
                                <ClearChatButton className={styles.settingsButton} onClick={clearAgentChat} disabled={!lastAgentQuestionRef.current || isLoading} />
                                <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            </div>
                            <div className={styles.commandsContainer}>
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors  tokens={innerStackTokens}>
                                    <Stack.Item grow styles={stackItemStyles}>
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
                            <h1 className={styles.oneshotTitle}>Ask your Agent</h1>
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
                                <ExampleList onExampleClicked={onExampleClicked}
                                    EXAMPLES={
                                        exampleList
                                } />
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
                </Pivot>
            </div>
        </div>
    );
};

export default SmartAgent;