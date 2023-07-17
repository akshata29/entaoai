import { useRef, useState, useEffect } from "react";
import { Checkbox, ChoiceGroup, IChoiceGroupOption, Panel, DefaultButton, Spinner, TextField, SpinButton, Stack, 
    IPivotItemProps, getFadedOverflowStyle, on} from "@fluentui/react";
import { ShieldLockRegular } from "@fluentui/react-icons";

import styles from "./Pib.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { askApi, askAgentApi, askTaskAgentApi, Approaches, AskResponse, AskRequest, refreshIndex, getSpeechApi, 
    summaryAndQa, getPib, getUserInfo } from "../../api";
import { Label } from '@fluentui/react/lib/Label';
import { Pivot, PivotItem } from '@fluentui/react';
import { IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { DetailsList, DetailsListLayoutMode, SelectionMode, ConstrainMode } from '@fluentui/react/lib/DetailsList';
import { mergeStyleSets } from '@fluentui/react/lib/Styling';
import { Amex } from "../../components/Symbols/Amex";
import { Nasdaq } from "../../components/Symbols/Nasdaq";
import { Nyse } from "../../components/Symbols/Nyse";
import { PrimaryButton } from "@fluentui/react";


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

    // Tokens definition
    const outerStackTokens: IStackTokens = { childrenGap: 5 };
    const innerStackTokens: IStackTokens = {
        childrenGap: 5,
        padding: 10,
    };

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

    useEffect(() => {
        setSelectedExchange(exchangeOptions[0])
        setSelectedCompany(amexTickers[0]);
        if (window.location.hostname != "localhost") {
            getUserInfoList();
            setShowAuthMessage(true)
        } else
            setShowAuthMessage(false)
    }, [])


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
                </Pivot>
            </div>
            )}
        </div>
    );
};

export default Pib;

