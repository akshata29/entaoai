import { useRef, useState, useEffect } from "react";
import { Panel, DefaultButton, Spinner, SpinButton, Stack } from "@fluentui/react";

import styles from "./SqlAgent.module.css";
import { IStyleSet, ILabelStyles, IPivotItemProps, Pivot, PivotItem } from '@fluentui/react';

import { sqlChat, AskResponse, sqlChain } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ExampleList, ExampleModel } from "../../components/Example";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";

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

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<AskResponse>();
    const [errorChain, setErrorChain] = useState<unknown>();
    const [answerChain, setAnswerChain] = useState<AskResponse>();

    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [summary, setSummary] = useState<string>();
    const [qa, setQa] = useState<string>('');
    const [exampleLoading, setExampleLoading] = useState(false)


    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const result = await sqlChat(question, retrieveCount);
            setAnswer(result);
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
            const result = await sqlChain(question, retrieveCount);
            setAnswerChain(result);
            if (result.error) {
                setErrorChain(result.error);
            }
        } catch (e) {
            setErrorChain(e);
        } finally {
            setIsLoading(false);
        }
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

    useEffect(() => {
        documentSummaryAndQa()
    }, [])

    return (
        <div className={styles.root}>
            <div className={styles.oneshotContainer}>
            <Pivot aria-label="Chat">
                    <PivotItem
                        headerText="Agent"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                    <div className={styles.oneshotTopSection}>
                        <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                        <h1 className={styles.oneshotTitle}>Ask your SQL</h1>
                        <div className={styles.example}>
                            <p className={styles.exampleText}><b>Scenario</b> : {summary}</p>
                        </div>
                        <h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>
                        {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                        <ExampleList onExampleClicked={onExampleClicked}
                        EXAMPLES={
                            exampleList
                        } />
                        <div className={styles.oneshotQuestionInput}>
                            <QuestionInput
                                placeholder="Ask me anything"
                                disabled={isLoading}
                                onSend={question => makeApiRequest(question)}
                            />
                        </div>
                    </div>
                    <div className={styles.oneshotBottomSection}>
                        {isLoading && <Spinner label="Generating answer" />}
                        {!isLoading && answer && !error && (
                            <div>
                                <div className={styles.oneshotAnswerContainer}>
                                    <Stack horizontal horizontalAlign="space-between">
                                        <Answer
                                            answer={answer}
                                            onCitationClicked={x => onShowCitation(x)}
                                            onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                            onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
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
                                answer={answer}
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
                        <div className={styles.oneshotTopSection}>
                            <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            <h1 className={styles.oneshotTitle}>Ask your SQL</h1>
                            <div className={styles.example}>
                                <p className={styles.exampleText}><b>Scenario</b> : {summary}</p>
                            </div>
                            <h4 className={styles.chatEmptyStateSubtitle}>Ask anything or try from following example</h4>
                            {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                            <ExampleList onExampleClicked={onExampleChainClicked}
                            EXAMPLES={
                                exampleList
                            } />
                            <div className={styles.oneshotQuestionInput}>
                                <QuestionInput
                                    placeholder="Ask me anything"
                                    disabled={isLoading}
                                    onSend={question => makeApiChainRequest(question)}
                                />
                            </div>
                        </div>
                        <div className={styles.oneshotBottomSection}>
                            {isLoading && <Spinner label="Generating answer" />}
                            {!isLoading && answerChain && !errorChain && (
                                <div>
                                    <div className={styles.oneshotAnswerContainer}>
                                        <Stack horizontal horizontalAlign="space-between">
                                            <Answer
                                                answer={answerChain}
                                                onCitationClicked={x => onShowCitation(x)}
                                                onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                            />
                                        </Stack>                               
                                    </div>
                                </div>
                            )}
                            {errorChain ? (
                                <div className={styles.oneshotAnswerContainer}>
                                    <AnswerError error={errorChain.toString()} onRetry={() => makeApiChainRequest(lastQuestionChainRef.current)} />
                                </div>
                            ) : null}
                            {activeAnalysisPanelTab && answerChain && (
                                <AnalysisPanel
                                    className={styles.oneshotAnalysisPanel}
                                    activeCitation={activeCitation}
                                    onActiveTabChanged={x => onToggleTab(x)}
                                    citationHeight="600px"
                                    answer={answerChain}
                                    activeTab={activeAnalysisPanelTab}
                                />
                            )}
                        </div>
                    </PivotItem>
                </Pivot>
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
                        label="Retrieve this many documents from search:"
                        min={1}
                        max={100}
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
                </Panel>
            </div>
        </div>
    );
};

export default SqlAgent;

