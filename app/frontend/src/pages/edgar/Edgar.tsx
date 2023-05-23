import { useRef, useState, useEffect } from "react";
import { ChoiceGroup, IChoiceGroupOption, Spinner } from "@fluentui/react";
import { TextField, PrimaryButton, Label, DefaultPalette, Stack, IStackStyles, IStackTokens } from "@fluentui/react";
import { Checkbox, Panel, DefaultButton,  SpinButton } from "@fluentui/react";

import styles from "./Edgar.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { secSearch, AskResponse, AskRequest } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { ExampleList, ExampleModel } from "../../components/Example";
import { DetailsList, DetailsListLayoutMode, Selection, SelectionMode, IColumn } from '@fluentui/react/lib/DetailsList';
import { Link } from '@fluentui/react/lib/Link';
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";

type Item = {
    company:  { label: string; };
    filingLink:  { label: string; };
    contentSummary:  { label: string; };
    filingDate:  { label: string; };
    filingType:  { label: string; };
    reportPeriod:  { label: string; };
    content:  { label: string; };
  };

const Edgar = () => {
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();

    const lastQuestionRef = useRef<string>("");

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<AskResponse>();
    const [items, setItems] = useState<Item[]>([]);

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    //const [selectedIndex, setSelectedIndex] = useState<IDropdownOption>();
    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [exampleLoading, setExampleLoading] = useState(false)     

    const [selectedEmbeddingItem, setSelectedEmbeddingItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [chainTypeOptions, setChainTypeOptions] = useState<any>([])
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();
    const [retrieveCount, setRetrieveCount] = useState<number>(3);

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

    const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedChain(item);
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "3"));
    };

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedEmbeddingItem(item);
    };

    const columns: IColumn[] = [
        {
          key: 'company',
          name: 'Company',
          fieldName: 'company',
          minWidth: 150,
          isMultiline: true,
        },
        {
            key: 'filingDate',
            name: 'Filing Date',
            fieldName: 'filingDate',
            minWidth: 80
        },
        {
            key: 'filingType',
            name: 'Filing Type',
            fieldName: 'filingType',
            minWidth: 80
        },
        {
          key: 'summary',
          name: 'Summary',
          isMultiline: true,
          minWidth: 900,
          isResizable: true,
          fieldName: 'contentSummary',
        },
        // {
        //     key: 'content',
        //     name: 'Content',
        //     isMultiline: true,
        //     minWidth: 900,
        //     isResizable: true,
        //     fieldName: 'content',
        // },
        {
            key: 'filingLink',
            name: 'Filings Link',
            fieldName: 'filingLink',
            minWidth: 100,
            isResizable: true,
            onRender: item => (
                // eslint-disable-next-line react/jsx-no-bind
                <Link href={item.filingLink}>
                  View
                </Link>
              ),
        }  
    ];
  
   
    const makeApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const result = await secSearch('cogsearchvs', 'secdocs', question, String(retrieveCount), String(selectedEmbeddingItem?.key));
            
            const itemsResponse: Item[] = [];
            console.log(result.values[0].data.text);
            result.values[0].data.text.forEach((item: { company: any; completeFilingLink: any; contentSummary: any; filingDate: any; filingType: any; reportPeriod: any; content:any }) => {
                itemsResponse.push({
                    company: item.company,
                    filingLink: item.completeFilingLink,
                    contentSummary: item.contentSummary,
                    content: item.content,
                    filingDate: item.filingDate,
                    filingType: item.filingType,
                    reportPeriod: item.reportPeriod,
                });
            });
            setItems(itemsResponse);
            console.log(itemsResponse)
            //setAnswer(result);
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const onToggleTab = (tab: AnalysisPanelTabs) => {
        if (activeAnalysisPanelTab === tab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);
        }
    };

    useEffect(() => {
        setSelectedEmbeddingItem(embeddingOptions[0])
        setChainTypeOptions(chainType)
        setSelectedChain(chainType[0])
    }, []);

    return (
        <div >
            <div >
                <div className={styles.commandsContainer}>
                        <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                </div>
                <div className={styles.edgarTopSection}>
                    <h1 className={styles.edgarTitle}>Ask your financial data</h1>
                    <div className={styles.edgarQuestionInput}>
                        <QuestionInput
                            placeholder="Ask me anything"
                            disabled={isLoading}
                            onSend={question => makeApiRequest(question)}
                        />
                    </div>
                </div>
                <div className={styles.edgarBottomSection}>
                    {isLoading && <Spinner label="Generating answer" />}
                    {!isLoading && !error && (
                        <div>
                            <div >
                                <DetailsList
                                    compact={true}
                                    items={items}
                                    columns={columns}
                                    setKey="multiple"
                                    selectionMode={SelectionMode.none}
                                    layoutMode={DetailsListLayoutMode.justified}
                                    isHeaderVisible={true}
                                    enterModalSelectionOnTouch={true}
                                />
                            </div>
                        </div>
                    )}
                    {error ? (
                        <div className={styles.edgarAnswerContainer}>
                            <AnswerError error={error.toString()} onRetry={() => makeApiRequest(lastQuestionRef.current)} />
                        </div>
                    ) : null}
                    {activeAnalysisPanelTab && answer && (
                        <AnalysisPanel
                            className={styles.edgarAnalysisPanel}
                            activeCitation={activeCitation}
                            onActiveTabChanged={x => onToggleTab(x)}
                            citationHeight="600px"
                            answer={answer}
                            activeTab={activeAnalysisPanelTab}
                        />
                    )}
                </div>
            </div>
            <Panel
                headerText="Configure Speech settings"
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
                    <br/>
                    <SpinButton
                        className={styles.edgarSettingsSeparator}
                        label="Retrieve this many documents from search:"
                        min={1}
                        max={10}
                        defaultValue={retrieveCount.toString()}
                        onChange={onRetrieveCountChange}
                    />
                    <br/>
                    <Dropdown 
                        label="Chain Type"
                        onChange={onChainChange}
                        selectedKey={selectedChain ? selectedChain.key : 'stuff'}
                        options={chainTypeOptions}
                        defaultSelectedKey={'stuff'}
                        styles={dropdownStyles}
                    />
                </div>
                <br/>
            </Panel>
        </div>
    );
};

export default Edgar;

