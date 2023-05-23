import { useRef, useState, useEffect } from "react";
import { Checkbox, Panel, DefaultButton, Spinner, SpinButton, Stack, Label } from "@fluentui/react";
import { Sparkle28Filled } from "@fluentui/react-icons";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import styles from "./SqlAgent.module.css";
import { Pivot, PivotItem } from '@fluentui/react';
import { SparkleFilled } from "@fluentui/react-icons";

import { sqlChat, AskResponse, sqlChain, getSpeechApi } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ExampleList, ExampleModel } from "../../components/Example";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";
import { ClearChatButton } from "../../components/ClearChatButton";
import { SqlViewer } from "../../components/SqlViewer";
import { DataTable } from "../../components/DataTable/DataTable";

var audio = new Audio();

const SqlAgent = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplatePrefix, setPromptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix, setPromptTemplateSuffix] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(10);
    const [temperature, setTemperature] = useState<number>(0.3);
    const [tokenLength, setTokenLength] = useState<number>(500);

    const [activeCitation, setActiveCitation] = useState<string>();

    const lastQuestionRef = useRef<string>("");
    const lastQuestionChainRef = useRef<string>("");
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    //const [answer, setAnswer] = useState<AskResponse>();
    const [answer, setAnswer] = useState<[AskResponse, string | null]>();
    const [errorChain, setErrorChain] = useState<unknown>();
    //const [answerChain, setAnswerChain] = useState<AskResponse>();
    const [answerChain, setAnswerChain] = useState<[AskResponse, string | null]>();
    const [useAutoSpeakAnswers, setUseAutoSpeakAnswers] = useState<boolean>(false);
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };


    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [summary, setSummary] = useState<string>();
    const [qa, setQa] = useState<string>('');
    const [sqlQuery, setSqlQuery] = useState<string>('');
    const [sqlData, setSqlData] = useState<Record<string, string | boolean | number>[]>([]);
    const [exampleLoading, setExampleLoading] = useState(false)

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

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItem(item);
    };
    
    const startSynthesis = async (answerType:string, url: string | null) => {
        if(isSpeaking) {
            audio.pause();
            setIsSpeaking(false);
        }

        if(url === null) {
            let speechAnswer;
            if (answerType == "Agent")
                speechAnswer = answer && answer[0].answer;
            else if (answerType == "Chain")
                speechAnswer = answerChain && answerChain[0].answer;

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

    const stopSynthesis = () => {
        audio.pause();
        setIsSpeaking(false);
    };

    const getSqlViewerContent = (question: string) => {
		if (sqlQuery) {
			if (isLoading) {
				return `-- ${question}`;
			} else {
				return `-- ${question} \n${sqlQuery}`;
			}
		}

		if (isLoading) {
			return `-- ${question}`;
		}

		return "-- No prompt yet";
	};

    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const result = await sqlChat(question, retrieveCount, String(selectedEmbeddingItem?.key));
            setSqlQuery(result.toolInput? result.toolInput : '');
            const dataTable:  Record<string, string | boolean | number>[] = []
            result.observation?.slice(1, -1).split('), (').forEach(function(el){
                const columns = el.split(',');
                var item : any = {}
                for (var i = 0; i < columns.length; i++) {
                    const colName = "col" + String(i)
                    var char = columns[i][0]
                    let colValue = columns[i];
                    if (char == '(') {
                        colValue = columns[i].slice(1);
                    } else if (char == "),") {
                        colValue = columns[i].slice(0, -1);
                    } else {
                        colValue = columns[i];
                    }

                    if (colValue.trim() == "," || colValue.trim() == "" || colValue.trim() == ")," || colValue.trim() == ")")
                    {
                    } else {
                        colValue = colValue.trim().replace(")", "").replace("Decimal(", "")
                        colValue = colValue.replace("'", "").replace("'", "").replace(")", "")
                        item[colName] = colValue
                    }
                }
                dataTable.push(item) 
            });

            setSqlData(dataTable);
            //setAnswer(result);
            setAnswer([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setAnswer([result, speechUrl]);
                startSynthesis("Agent", speechUrl);
            }

            if (result.error) {
                setError(result.error);
            }
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const makeApiChainRequest = async (question: string) => {
        lastQuestionChainRef.current = question;

        errorChain && setErrorChain(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const result = await sqlChain(question, retrieveCount, String(selectedEmbeddingItem?.key));
            setSqlQuery(result.toolInput? result.toolInput : '');
            const dataTable: Record<string, string | boolean | number>[] = []
            result.observation?.slice(1, -1).split('), (').forEach(function(el){
                const columns = el.split(',');
                let rowValues = ''
                var item: any = {}
                for (var i = 0; i < columns.length; i++) {
                    const colName = "col" + String(i)
                    var char = columns[i][0]
                    let colValue = columns[i];
                    if (char == '(') {
                        colValue = columns[i].slice(1);
                    } else if (char == "),") {
                        colValue = columns[i].slice(0, -1);
                    } else {
                        colValue = columns[i];
                    }

                    if (colValue.trim() == "," || colValue.trim() == "" || colValue.trim() == ")," || colValue.trim() == ")")
                    {
                    } else {
                        colValue = colValue.trim().replace(")", "").replace("Decimal(", "")
                        colValue = colValue.replace("'", "").replace("'", "").replace(")", "")
                        item[colName] = colValue
                    }
                }
                dataTable.push(item) 
            });

            setSqlData(dataTable);
            //setAnswerChain(result);
            setAnswerChain([result, null]);
            if(useAutoSpeakAnswers) {
                const speechUrl = await getSpeechApi(result.answer);
                setAnswerChain([result, speechUrl]);
                startSynthesis("Chain", speechUrl);
            }
            if (result.error) {
                setErrorChain(result.error);
            }
        } catch (e) {
            setErrorChain(e);
        } finally {
            setIsLoading(false);
        }
    };

    const onEnableAutoSpeakAnswersChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseAutoSpeakAnswers(!!checked);
    };

    const onPromptTemplateChange = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplate(newValue || "");
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
        setTokenLength(parseInt(newValue || "500"));
    };

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onExampleChainClicked = (example: string) => {
        makeApiChainRequest(example);
    };

    const onToggleTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab === tab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }
    };

    const onShowCitation = (citation: string) => {
    };

    const documentSummaryAndQa = async () => {
        const sampleQuestion = []
        const  questionList = [] 
        questionList.push("What products are available")
        questionList.push("Which shippers can ship the orders?")
        questionList.push("How many shipment Speedy Express did?")
        questionList.push("How many customers did placed an order")
        questionList.push("For the year 1996 give me subtotals for each order")
        questionList.push("Show me the Sales by Year")
        questionList.push("Which employee did largest order")
        questionList.push("get an alphabetical list of products.")
        questionList.push("List the discontinued products")
        questionList.push("calculates sales price for each order after discount is applied")
        questionList.push("Show top 10 Products by Category")
        questionList.push("Display Products by Category")
        questionList.push("Top 10 Customer and Suppliers by City")
        questionList.push("List of the Products that are above average price")
        questionList.push("List of the Products that are above average price, also show average price for each product")
        questionList.push("Number of units in stock by category and supplier continent")

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
        setExampleLoading(false)

        const summary = "This use-case showcases how using the prompt engineering approach from Chain of Thought modelling we can make "
        + " it scalable and further use LLM's capability of generating SQL Code from Natural Language by providing the context  "
        + " without the need to know the DB schema before hand.  "
        + " For this use-case we are using the Northwind sample database (https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/northwind-pubs) "
        + " that is hosted in Azure SQL, but you can easily change it to instead use Synapse (Dedicated or Serverless) to query against the data in Lakehouse."
        + " Ask the question based on the ERD of Northwind Sample database at https://en.wikiversity.org/wiki/Database_Examples/Northwind"
        setSummary(summary)

    }

    const clearChat = () => {
        lastQuestionRef.current = "";
        error && setError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswer(undefined);
    };

    const clearChainChat = () => {
        lastQuestionChainRef.current = "";
        errorChain && setErrorChain(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setAnswerChain(undefined);
    };

    useEffect(() => {
        documentSummaryAndQa()
        setSelectedEmbeddingItem(embeddingOptions[0])
    }, [])

    return (
        <div className={styles.root}>
            <div className={styles.sqlAgentContainer}>
                <Pivot aria-label="Chat">
                    <PivotItem
                        headerText="Agent"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                    <div className={styles.sqlAgentTopSection}>
                        <div className={styles.commandsContainer}>
                            <ClearChatButton className={styles.settingsButton} onClick={clearChat} disabled={!lastQuestionRef.current || isLoading} />
                            <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                        </div>
                        <SparkleFilled fontSize={"30px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" />
                        <h1 className={styles.sqlAgentTitle}>Ask your SQL</h1>
                        <div className={styles.example}>
                            <p className={styles.exampleText}><b>Scenario</b> : {summary}</p>
                        </div>
                        <h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>
                        <div className={styles.sqlAgentQuestionInput}>
                            <QuestionInput
                                placeholder="Ask me anything"
                                disabled={isLoading}
                                updateQuestion={lastQuestionRef.current}
                                onSend={question => makeApiRequest(question)}
                            />
                        </div>
                        {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                        <ExampleList onExampleClicked={onExampleClicked}
                            EXAMPLES={
                                exampleList
                        } />
                    </div>
                    <div className={styles.sqlAgentBottomSection}>
                        {isLoading && <Spinner label="Generating answer" />}
                        {!isLoading && answer && !error && (
                            <div>
                                <div className={styles.sqlAgentAnswerContainer}>
                                    <Stack horizontal horizontalAlign="space-between">
                                        <Pivot aria-label="Chat">
                                            <PivotItem
                                                headerText="Answer"
                                                headerButtonProps={{
                                                'data-order': 1,
                                                }}
                                            >
                                                <Answer
                                                    //answer={answer}
                                                    answer={answer[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("Agent", answer[1])}
                                                />
                                            </PivotItem>
                                            <PivotItem
                                                headerText="SQL Query"
                                                headerButtonProps={{
                                                'data-order': 2,
                                                }}
                                            >
                                                <Stack className={`${styles.answerContainer}`} verticalAlign="space-between">
                                                    <Stack.Item>
                                                        <Stack horizontal horizontalAlign="space-between">
                                                            <Sparkle28Filled primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Answer logo" />
                                                        </Stack>
                                                    </Stack.Item>
                                                    <Stack.Item>
                                                        <div className={styles.answerText}>
                                                            <SqlViewer content={getSqlViewerContent(lastQuestionRef.current)} />
                                                        </div>
                                                    </Stack.Item>
                                                </Stack>
                                            </PivotItem>
                                            <PivotItem
                                                headerText="SQL Data"
                                                headerButtonProps={{
                                                'data-order': 3,
                                                }}
                                            >
                                                <Stack className={`${styles.answerContainer}`} verticalAlign="space-between">
                                                    <Stack.Item>
                                                        <Stack horizontal horizontalAlign="space-between">
                                                            <Sparkle28Filled primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Answer logo" />
                                                        </Stack>
                                                    </Stack.Item>
                                                    <Stack.Item>
                                                        <div className={styles.answerText}>
                                                            <DataTable data={sqlData} />
                                                        </div>
                                                    </Stack.Item>
                                                </Stack>

                                            </PivotItem>
                                        </Pivot>
                                    </Stack>                               
                                </div>
                            </div>
                        )}
                        {error ? (
                            <div className={styles.sqlAgentAnswerContainer}>
                                <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                            </div>
                        ) : null}
                        {activeAnalysisPanelTab && answer && (
                            <AnalysisPanel
                                className={styles.sqlAgentAnalysisPanel}
                                activeCitation={activeCitation}
                                onActiveTabChanged={x => onToggleTab(x)}
                                citationHeight="600px"
                                //answer={answer}
                                answer={answer[0]}
                                activeTab={activeAnalysisPanelTab}
                            />
                        )}
                    </div>
                    </PivotItem>
                    <PivotItem
                        headerText="Database Chain"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                        <div className={styles.sqlAgentTopSection}>
                            <div className={styles.commandsContainer}>
                                <ClearChatButton className={styles.settingsButton} onClick={clearChainChat} disabled={!lastQuestionChainRef.current || isLoading} />
                                <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            </div>
                            <SparkleFilled fontSize={"30px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" />
                            <h1 className={styles.sqlAgentTitle}>Ask your SQL</h1>
                            <div className={styles.example}>
                                <p className={styles.exampleText}><b>Scenario</b> : {summary}</p>
                            </div>
                            <h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>
                            <div className={styles.sqlAgentQuestionInput}>
                                <QuestionInput
                                    placeholder="Ask me anything"
                                    disabled={isLoading}
                                    updateQuestion={lastQuestionChainRef.current}
                                    onSend={question => makeApiChainRequest(question)}
                                />
                            </div>
                            {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                            {/* {!answerChain && (
                                <ExampleList onExampleClicked={onExampleChainClicked}
                                EXAMPLES={
                                    exampleList
                                } />
                            )}
                             */}
                            <ExampleList onExampleClicked={onExampleChainClicked}
                                EXAMPLES={
                                    exampleList
                                } />
                        </div>
                        <div className={styles.sqlAgentBottomSection}>
                            {isLoading && <Spinner label="Generating answer" />}
                            {!isLoading && answerChain && !errorChain && (
                                <div>
                                    <div className={styles.sqlAgentAnswerContainer}>
                                        <Stack horizontal horizontalAlign="space-between">
                                        <Pivot aria-label="Chat">
                                            <PivotItem
                                                headerText="Answer"
                                                headerButtonProps={{
                                                'data-order': 1,
                                                }}
                                            >
                                                <Answer
                                                    //answer={answerChain}
                                                    answer={answerChain[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("Chain", answerChain[1])}
                                                />
                                            </PivotItem>
                                            <PivotItem
                                                headerText="SQL Query"
                                                headerButtonProps={{
                                                'data-order': 2,
                                                }}
                                            >
                                                <Stack className={`${styles.answerContainer}`} verticalAlign="space-between">
                                                    <Stack.Item>
                                                        <Stack horizontal horizontalAlign="space-between">
                                                            <Sparkle28Filled primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Answer logo" />
                                                        </Stack>
                                                    </Stack.Item>
                                                    <Stack.Item>
                                                        <div className={styles.answerText}>
                                                            <SqlViewer content={getSqlViewerContent(lastQuestionChainRef.current)} />
                                                        </div>
                                                    </Stack.Item>
                                                </Stack>
                                            </PivotItem>
                                            <PivotItem
                                                headerText="SQL Data"
                                                headerButtonProps={{
                                                'data-order': 3,
                                                }}
                                            >
                                                <Stack className={`${styles.answerContainer}`} verticalAlign="space-between">
                                                    <Stack.Item>
                                                        <Stack horizontal horizontalAlign="space-between">
                                                            <Sparkle28Filled primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Answer logo" />
                                                        </Stack>
                                                    </Stack.Item>
                                                    <Stack.Item>
                                                        <div className={styles.answerText}>
                                                            <DataTable data={sqlData} />
                                                        </div>
                                                    </Stack.Item>
                                                </Stack>

                                            </PivotItem>
                                        </Pivot>
                                        </Stack>                               
                                    </div>
                                </div>
                            )}
                            {errorChain ? (
                                <div className={styles.sqlAgentAnswerContainer}>
                                    <AnswerError error={errorChain.toString()} onRetry={() => makeApiChainRequest(lastQuestionChainRef.current)} />
                                </div>
                            ) : null}
                            {activeAnalysisPanelTab && answerChain && (
                                <AnalysisPanel
                                    className={styles.sqlAgentAnalysisPanel}
                                    activeCitation={activeCitation}
                                    onActiveTabChanged={x => onToggleTab(x)}
                                    citationHeight="600px"
                                    //answer={answerChain}
                                    answer={answerChain[0]}
                                    activeTab={activeAnalysisPanelTab}
                                />
                            )}
                        </div>
                    </PivotItem>
                </Pivot>
                <Panel
                    headerText="Configure SQL NLP"
                    isOpen={isConfigPanelOpen}
                    isBlocking={false}
                    onDismiss={() => setIsConfigPanelOpen(false)}
                    closeButtonAriaLabel="Close"
                    onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                    isFooterAtBottom={true}
                >
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
                    <br/>
                    <SpinButton
                        className={styles.sqlAgentSettingsSeparator}
                        label="Retrieve this many documents from search:"
                        min={1}
                        max={100}
                        defaultValue={retrieveCount.toString()}
                        onChange={onRetrieveCountChange}
                    />
                    <SpinButton
                        className={styles.sqlAgentSettingsSeparator}
                        label="Set the Temperature:"
                        min={0.0}
                        max={1.0}
                        defaultValue={temperature.toString()}
                        onChange={onTemperatureChange}
                    />
                    <SpinButton
                        className={styles.sqlAgentSettingsSeparator}
                        label="Max Length (Tokens):"
                        min={0}
                        max={4000}
                        defaultValue={tokenLength.toString()}
                        onChange={onTokenLengthChange}
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
    );
};

export default SqlAgent;

