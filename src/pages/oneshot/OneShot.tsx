import { useRef, useState, useEffect } from "react";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, Stack } from "@fluentui/react";

import styles from "./OneShot.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { askApi, Approaches, AskResponse, AskRequest } from "../../api";
import { Answer, AnswerError } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { BlobServiceClient } from "@azure/storage-blob";

const containerName = `chatpdf`
const sasToken = "?sv=2021-12-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2024-03-16T05:34:46Z&st=2023-03-15T21:34:46Z&spr=https&sig=tyHUI9FoEo2PaQR6Ox%2FdQYfR3jFzVzvB2J7VbD5TXDQ%3D"
const storageAccountName = "dataaiopenaistor"
const uploadUrl = `https://${storageAccountName}.blob.core.windows.net/?${sasToken}`;

const OneShot = () => {
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [approach, setApproach] = useState<Approaches>(Approaches.RetrieveThenRead);
    const [promptTemplate, setPromptTemplate] = useState<string>("");
    const [promptTemplatePrefix, setPromptTemplatePrefix] = useState<string>("");
    const [promptTemplateSuffix, setPromptTemplateSuffix] = useState<string>("");
    const [retrieveCount, setRetrieveCount] = useState<number>(3);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");

    const [options, setOptions] = useState<any>([])
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };

    const lastQuestionRef = useRef<string>("");

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<AskResponse>();
    const [mapReduceAnswer, setMapReduceAnswer] = useState<AskResponse>();
    const [refineAnswer, setRefineAnswer] = useState<AskResponse>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

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
                    excludeCategory: excludeCategory.length === 0 ? undefined : excludeCategory,
                    top: retrieveCount,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions
                }
            };
            const result = await askApi(request, String(selectedItem?.key), 'pinecone', 'stuff');
            setAnswer(result);
            // const mapReduceResult = await askApi(request, selectedItem?.key, 'pinecone', 'map-reduce');
            // setMapReduceAnswer(mapReduceResult);
            // const refineResult = await askApi(request, selectedItem?.key, 'pinecone', 'refine');
            // setRefineAnswer(refineResult);
        } catch (e) {
            setError(e);
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

    const onApproachChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        setApproach((option?.key as Approaches) || Approaches.RetrieveThenRead);
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

    const onExampleClicked = (example: string) => {
        makeApiRequest(example);
    };

    const onShowCitation = (citation: string) => {
        if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab) {
            setActiveAnalysisPanelTab(undefined);
        } else {
            setActiveCitation(citation);
            setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
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
        const blobServiceClient = new BlobServiceClient(uploadUrl)
        const containerClient = blobServiceClient.getContainerClient(containerName)
    
        const listOptions = {
          includeDeleted: false, // include deleted blobs
          includeDeletedWithVersions: false, // include deleted blobs with versions
          includeLegalHost: false, // include legal host id
          includeMetadata: true, // include custom metadata
          includeSnapshots: false, // include snapshots
          includeTags: true, // include indexable tags
          includeUncommittedBlobs: false, // include uncommitted blobs
          includeVersions: false, // include all blob version
          prefix: '' // filter by blob name prefix
        }
    
        const files = []
    
        const blobs = containerClient.listBlobsFlat(listOptions)
        for await (const blob of blobs) {
          if (blob.metadata?.embedded == "true")
          {
            files.push({
                text: blob.name,
                key: blob.metadata?.namespace
            })
          }
        }
        setOptions(files)
        setSelectedItem(files[0])
    }

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedItem(item);
    };

    useEffect(() => {
        refreshBlob()
    }, [])

    const approaches: IChoiceGroupOption[] = [
        {
            key: Approaches.RetrieveThenRead,
            text: "Retrieve-Then-Read"
        },
        {
            key: Approaches.ReadRetrieveRead,
            text: "Read-Retrieve-Read"
        },
        {
            key: Approaches.ReadDecomposeAsk,
            text: "Read-Decompose-Ask"
        }
    ];

    return (
        <div className={styles.root}>
            <div>
            <div className={styles.commandsContainer}>
                <DefaultButton onClick={refreshBlob}>Refresh PDF & Index</DefaultButton>
                <Dropdown
                    selectedKey={selectedItem ? selectedItem.key : undefined}
                    // eslint-disable-next-line react/jsx-no-bind
                    onChange={onChange}
                    placeholder="Select an PDF"
                    options={options}
                    styles={dropdownStyles}
                />
            </div>
            </div>
            <div className={styles.oneshotContainer}>
                <div className={styles.oneshotTopSection}>
                    <h1 className={styles.oneshotTitle}>Ask your data</h1>
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
                                     {/* <Answer
                                        answer={mapReduceAnswer}
                                        onCitationClicked={x => onShowCitation(x)}
                                        onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                        onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                    />
                                    <Answer
                                        answer={refineAnswer}
                                        onCitationClicked={x => onShowCitation(x)}
                                        onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                        onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                    /> */}
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

                <Panel
                    headerText="Configure answer generation"
                    isOpen={isConfigPanelOpen}
                    isBlocking={false}
                    onDismiss={() => setIsConfigPanelOpen(false)}
                    closeButtonAriaLabel="Close"
                    onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                    isFooterAtBottom={true}
                >
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
                        max={50}
                        defaultValue={retrieveCount.toString()}
                        onChange={onRetrieveCountChange}
                    />
                    <TextField className={styles.oneshotSettingsSeparator} label="Exclude category" onChange={onExcludeCategoryChanged} />
                    <Checkbox
                        className={styles.oneshotSettingsSeparator}
                        checked={useSemanticRanker}
                        label="Use semantic ranker for retrieval"
                        onChange={onUseSemanticRankerChange}
                    />
                    <Checkbox
                        className={styles.oneshotSettingsSeparator}
                        checked={useSemanticCaptions}
                        label="Use query-contextual summaries instead of whole documents"
                        onChange={onUseSemanticCaptionsChange}
                        disabled={!useSemanticRanker}
                    />
                </Panel>
            </div>
        </div>
    );
};

export default OneShot;
