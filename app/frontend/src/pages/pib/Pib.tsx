import { useRef, useState, useEffect, useMemo } from "react";
import { DefaultButton, Spinner, TextField, SpinButton, Stack, ITextStyles, Checkbox, Panel} from "@fluentui/react";
import { News16Filled, ShieldLockRegular } from "@fluentui/react-icons";
import { SparkleFilled } from "@fluentui/react-icons";

import styles from "./Pib.module.css";
import { Dropdown, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { AskResponse,  chatGpt, getPib, getUserInfo, Approaches, getNews, getSocialSentiment, getIncomeStatement, getCashFlow } from "../../api";
import { pibChatGptApi, ChatRequest, ChatTurn, getAllIndexSessions, getIndexSession, getIndexSessionDetail, deleteIndexSession, renameIndexSession } from "../../api";
import { SettingsButton } from "../../components/SettingsButton";
import { AnswerChat } from "../../components/Answer/AnswerChat";
import { Label } from '@fluentui/react/lib/Label';
import { Pivot, PivotItem } from '@fluentui/react';
import { IStackStyles, IStackTokens, IStackItemStyles } from '@fluentui/react/lib/Stack';
import { DefaultPalette, mergeStyleSets } from '@fluentui/react/lib/Styling';
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
import { DetailsList, DetailsListLayoutMode, SelectionMode, Selection, IColumn} from '@fluentui/react/lib/DetailsList';
import { Image, ImageFit } from '@fluentui/react/lib/Image';
import { Link } from '@fluentui/react/lib/Link';
import {  LineChart, GroupedVerticalBarChart, IGroupedVerticalBarChartProps } from '@fluentui/react-charting';
import pptxgen from "pptxgenjs";
import Downshift from "downshift"

const Pib = () => {

    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 400 } };
    const dropdownShortStyles: Partial<IDropdownStyles> = { dropdown: { width: 150 } };

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<unknown>();

    const [symbol, setSymbol] = useState<string>('AAPL');
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
    const [summaryTranscript, setSummaryTranscript] = useState<string>();
    const [pressReleases, setPressReleases] = useState<any>();
    const [secFilings, setSecFilings] = useState<any>();
    const [researchReport, setResearchReports] = useState<any>();

    const lastQuestionRef = useRef<string>("");
    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);
    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [answers, setAnswers] = useState<[user: string, response: AskResponse, speechUrl: string | null][]>([]);
    const [runningIndex, setRunningIndex] = useState<number>(-1);
    const [chatSession, setChatSession] = useState<ChatSession | null>(null);
    const [selectedItems, setSelectedItems] = useState<any[]>([]);
    const [sessionName, setSessionName] = useState<string>('');
    const [sessionList, setSessionList] = useState<any[]>();
    const [oldSessionName, setOldSessionName] = useState<string>('');
    const [sessionId, setSessionId] = useState<string>();
    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);
    const [selectedDoc, setSelectedDoc] = useState<IDropdownOption>();
    const [stockNews, setStockNews] = useState<any>();
    const [socialSentiment, setSocialSentiment] = useState<any>(null);
    const [incomeStatement, setIncomeStatement] = useState<any>();
    const [cashFlow, setCashFlow] = useState<any>();

    const [answersGpt, setAnswersGpt] = useState<[user: string, response: string, speechUrl: string | null][]>([]);
    const [chatSessionGpt, setChatSessionGpt] = useState<ChatSession | null>(null);
    const [sessionListGpt, setSessionListGpt] = useState<any[]>();
    const lastQuestionRefGpt = useRef<string>("");
    const [useInternet, setUseInternet] = useState(false);
    const [isConfigPanelOpenGpt, setIsConfigPanelOpenGpt] = useState(false);
    const [promptTemplateGpt, setPromptTemplateGpt] = useState<string>("");
    const [sessionIdGpt, setSessionIdGpt] = useState<string>();
    const [sessionNameGpt, setSessionNameGpt] = useState<string>('');
    const [oldSessionNameGpt, setOldSessionNameGpt] = useState<string>('');
    const [selectedDeploymentTypeGpt, setSelectedDeploymentTypeGpt] = useState<IDropdownOption>();
    const [selectedPromptTypeItemGpt, setSelectedPromptTypeItemGpt] = useState<IDropdownOption>();    
    const [selectedItemsGpt, setSelectedItemsGpt] = useState<any[]>([]);
    const [selectedEmbeddingItemGpt, setSelectedEmbeddingItemGpt] = useState<IDropdownOption>();
    const [temperatureGpt, setTemperatureGpt] = useState<number>(0.7);
    const [tokenLengthGpt, setTokenLengthGpt] = useState<number>(750);

    const lineMargins = { left: 35, top: 20, bottom: 35, right: 20 };
    const textStyles: Partial<ITextStyles> = { root: { width: 1200, height: 300 } };

    const deploymentTypeGptOptions = [
        {
          key: 'gpt35',
          text: 'GPT 3.5 Turbo'
        },
        {
          key: 'gpt3516k',
          text: 'GPT 3.5 Turbo - 16k'
        }
    ]
    const embeddingGptOptions = [
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
    const selectionGpt = useMemo(
        () =>
        new Selection({
            onSelectionChanged: () => {
            setSelectedItemsGpt(selection.getSelection());
        },
        selectionMode: SelectionMode.single,
        }),
    []);
    const sessionListGptColumn = [
        {
          key: 'Session Name',
          name: 'Session Name',
          fieldName: 'Session Name',
          minWidth: 100,
          maxWidth: 200, 
          isResizable: false,
        }
    ]
    const detailsListGpt = useMemo(
        () => (
            <MarqueeSelection selection={selectionGpt}>
                <DetailsList
                    className={styles.example}
                    items={sessionListGpt || []}
                    columns={sessionListGptColumn}
                    selectionMode={SelectionMode.single}
                    //getKey={(item: any) => item.key}
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
         [selectionGpt, sessionListGptColumn, sessionListGpt]
    );
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
    function stockNewsRenderColumn(item?: any, index?: number, column?: IColumn) {
        const fieldContent = item[column?.fieldName as keyof any] as string;
      
        switch (column?.key) {
          case 'thumbnail':
            return <Image src={fieldContent} width={50} height={50} imageFit={ImageFit.cover} />;
      
          case 'name':
            return <Link href="#">{fieldContent}</Link>;
            
          default:
            return <span>{fieldContent}</span>;
        }
    }
    const stockNewsColumns = [
        {
            key: 'thumbnail',
            name: '',
            fieldName: 'image',
            minWidth: 50, maxWidth: 70, isResizable: false, isMultiline: true
        },
        {
          key: 'title',
          name: 'Title',
          fieldName: 'title',
          minWidth: 200, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
            key: 'name',
            name: 'News Source',
            fieldName: 'url',
            minWidth: 200, maxWidth: 200, isResizable: false, isMultiline: true
        },
        {
          key: 'text',
          name: 'News Details',
          fieldName: 'text',
          minWidth: 300, maxWidth: 300, isResizable: false, isMultiline: true
        }
    ]
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
          name: 'Question or Topic',
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
                    //getKey={(item: any) => item.key}
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
    const generatePresentation = async () => {
        let pptx = new pptxgen();
        let slide = null;

        // Define Master Slide
        pptx.layout = "LAYOUT_WIDE";
        pptx.title = "Pib for " + symbol;
        pptx.company = "Microsoft";
        pptx.author = "Ashish Talati"
        pptx.subject = "Public Information Book"
        pptx.theme = { headFontFace: "Arial Light" };
        pptx.theme = { bodyFontFace: "Arial" };


        // Define Master slides for Tables
        pptx.defineSlideMaster({
            title: "PibMasterForTable",
            background: { fill: "F1F1F1" },
            margin: [0.5, 0.25, 1.0, 0.25],
            objects: [
                { rect: { x: 0.0, y: 6.9, w: "100%", h: 0.6, fill: { color: "003b75" } } },
                { image: { x: 11.45, y: 5.95, w: 1.67, h: 0.75, path: "Microsoft.png" } },
                {
                    placeholder: {
                        options: { name: "footer", type:'tbl', x: 0, y: 6.9, w: "100%", h: 0.6, align: "center", valign: "middle", color: "FFFFFF", fontSize: 12 },
                        text: "(footer placeholder)",
                    },
                },
            ],
            slideNumber: { x: 0.6, y: 7.1, color: "FFFFFF", fontFace: "Arial", fontSize: 10, align: "center" },
        });

        // Add Biography Slide
        slide = pptx.addSlide({ sectionTitle: "Biography", masterName: "PibMasterForTable" });
        slide.addText(
			[
				{ text: symbol + " : ", options: { fontSize: 14, color: "0088CC", bold: true } },
				{ text: "Biography of Executives", options: { fontSize: 13, color: "9F9F9F" } },
			],
			{ x: 0.5, y: 0.13, w: "90%" }
		);

        let arrRows : any[] = [];
        arrRows.push([
			{ text: "Name", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
			{ text: "Title", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
			{ text: "Biography", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
		]);

        biography.forEach((bio: { Name: any; Title: any; Biography: any; }) => {
            arrRows.push([
                bio.Name,
                bio.Title,
                bio.Biography
            ])
        })

        slide.addText("Overview & Biography", { placeholder: "footer" });
		slide.addTable(arrRows, { x: 1.0, y: 0.6, colW: [0.75, 1.75, 9], margin: 0.05, border: { color: "CFCFCF" }, autoPage: true, autoPageRepeatHeader: true });
		slide.newAutoPagedSlides.forEach((slide) => slide.addText("Overview & Biography", { placeholder: "footer" }));
        slide.newAutoPagedSlides.forEach((slide) => slide.addText([
            { text: symbol + " : ", options: { fontSize: 14, color: "0088CC", bold: true } },
            { text: "Biography of Executives", options: { fontSize: 13, color: "9F9F9F" } },
        ],
        { x: 0.5, y: 0.13, w: "90%" }));

        // Add Earning call Slide
        slide = pptx.addSlide({ sectionTitle: "Earning Call", masterName: "PibMasterForTable" });
        slide.addText(
			[
				{ text: symbol + " : ", options: { fontSize: 14, color: "0088CC", bold: true } },
				{ text: "Earning Call Summary", options: { fontSize: 13, color: "9F9F9F" } },
			],
			{ x: 0.5, y: 0.13, w: "90%" }
		);

        arrRows = [];
        arrRows.push([
			{ text: "Question or Topic", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
			{ text: "Answer or Summary", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
		]);

        transcriptQuestions.forEach((tr: { question: any; answer: any; }) => {
            arrRows.push([
                tr.question,
                tr.answer,
            ])
        })

        slide.addText("Earning Call Summary", { placeholder: "footer" });
		slide.addTable(arrRows, { x: 1.0, y: 0.6, colW: [1.75, 9], margin: 0.05, border: { color: "CFCFCF" }, autoPage: true, autoPageRepeatHeader: true });
        slide.newAutoPagedSlides.forEach((slide) => slide.addText("Earning Call Summary", { placeholder: "footer" }));
        slide.newAutoPagedSlides.forEach((slide) => slide.addText([
            { text: symbol + " : ", options: { fontSize: 14, color: "0088CC", bold: true } },
            { text: "Earning Call Summary", options: { fontSize: 13, color: "9F9F9F" } },
        ],
        { x: 0.5, y: 0.13, w: "90%" }));

        // Add Press Releases Slide
        slide = pptx.addSlide({ sectionTitle: "Press Releases", masterName: "PibMasterForTable" });
        slide.addText(
            [
                { text: symbol + " : ", options: { fontSize: 14, color: "0088CC", bold: true } },
                { text: "Press Releases Summary", options: { fontSize: 13, color: "9F9F9F" } },
            ],
            { x: 0.5, y: 0.13, w: "90%" }
        );

        arrRows = [];
        arrRows.push([
            { text: "Release Date", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
            { text: "Title", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
            { text: "Summary", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
            { text: "Sentiment", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
            { text: "Score", options: { fill: "0088cc", color: "ffffff", valign: "middle" } },
        ]);

        pressReleases.forEach((pr: { releaseDate: any; title: any; summary:any, sentiment:any, sentimentScore:any }) => {
            arrRows.push([
                pr.releaseDate,
                pr.title,
                pr.summary,
                pr.sentiment,
                pr.sentimentScore
            ])
        })

        slide.addText("Press Releases Summary", { placeholder: "footer" });
        slide.addTable(arrRows, { x: 0.2, y: 0.6, colW: [1.7, 2.75, 7, 1.2, 1.0], margin: 0.05, border: { color: "CFCFCF" }, autoPage: true, autoPageRepeatHeader: true });
        slide.newAutoPagedSlides.forEach((slide) => slide.addText("Press Releases Summary", { placeholder: "footer" }));
        slide.newAutoPagedSlides.forEach((slide) => slide.addText([
            { text: symbol + " : ", options: { fontSize: 14, color: "0088CC", bold: true } },
            { text: "Press Releases Summary", options: { fontSize: 13, color: "9F9F9F" } },
        ],
        { x: 0.5, y: 0.13, w: "90%" }));

        pptx.writeFile();

    }
    const processPib = async (step: string) => {
        try {
            setIsLoading(true);    
            if (step == '6') {
                    await getNews(symbol)

                    .then(async (response) => {
                        setStockNews(response)
                        await getSocialSentiment(symbol)
                        .then((sentimentResp : any) => {
                            const series1: { x: Date; y: any; }[] = []
                            const series2: { x: Date; y: any; }[] = []
                            const series3: { x: Date; y: any; }[] = []
                            const series4: { x: Date; y: any; }[] = []
                            const lineChartData = []
                            const socialSentimentData = []
                            sentimentResp.forEach((item: any) => {
                                series1.push({x: new Date(item.date), y: item.tweetSentiment})
                                series2.push({x: new Date(item.date), y: item.redditCommentSentiment})
                                series3.push({x: new Date(item.date), y: item.stocktwitsPostSentiment})
                                series4.push({x: new Date(item.date), y: item.yahooFinanceCommentSentiment})
                            })
                            lineChartData.push(
                                { legend: 'Twitter Sentiment', data: series1.reverse(), color: DefaultPalette.blue },
                            )
                            lineChartData.push(
                                { legend: 'Reddit Sentiment', data: series2.reverse(), color: DefaultPalette.green },
                            )
                            lineChartData.push(
                                { legend: 'Stock Twits Sentiment', data: series3.reverse(), color: DefaultPalette.red },
                            )
                            lineChartData.push(
                                { legend: 'Yahoo Finance Sentiment', data: series4.reverse(), color: DefaultPalette.yellow },
                            )
                            socialSentimentData.push(
                                { chartTitle: 'Social Sentiment', lineChartData: lineChartData },
                            )

                            setSocialSentiment(socialSentimentData[0])
                        })
                        .catch((error) => {
                            console.log(error)
                        })
                    })
                    .catch((error) => {
                        console.log(error)
                    })
            } 
            else if (step == '7') {
                await getIncomeStatement(symbol)
                .then(async (incResponse: any) => {
                    const incomeDataSeries: { name: string; series: { key: string; data: number; color: string; legend: string; }[]; }[] = []
                    incResponse.forEach((item: any) => {
                        incomeDataSeries.push({
                            name : String(new Date(item.date).getFullYear()),
                            series: [{
                                key: "Revenue",
                                data: item.revenue,
                                color: DefaultPalette.green,
                                legend: 'Revenue',
                                },
                                {
                                    key: "Income",
                                    data: item.netIncome,
                                    color: DefaultPalette.blue,
                                    legend: 'Net Income',
                                },
                                {
                                    key: "GrossProfit",
                                    data: item.grossProfit,
                                    color: DefaultPalette.yellow,
                                    legend: 'Gross Profit',
                                }
                            ]
                        }
                        )
                    })
                    setIncomeStatement(incomeDataSeries)
                    await getCashFlow(symbol)
                    .then((cfResponse : any) => {
                        const cfDataSeries: { name: string; series: { key: string; data: number; color: string; legend: string; }[]; }[] = []
                        cfResponse.forEach((item: any) => {
                            cfDataSeries.push({
                                name : String(new Date(item.date).getFullYear()),
                                series: [{
                                    key: "AP",
                                    data: item.accountsPayables,
                                    color: DefaultPalette.green,
                                    legend: 'Account Payable',
                                    },
                                    {
                                        key: "fcf",
                                        data: item.freeCashFlow,
                                        color: DefaultPalette.blue,
                                        legend: 'Free Cash Flow',
                                    },
                                    {
                                        key: "OcF",
                                        data: item.operatingCashFlow,
                                        color: DefaultPalette.yellow,
                                        legend: 'Operating Cash Flow',
                                    }
                                ]
                            }
                            )
                        })
                        setCashFlow(cfDataSeries)
                    })
                    .catch((error) => {
                        console.log(error)
                    })
                })
                .catch((error) => {
                    console.log(error)
                })
            }
            else 
            {
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
                                } else if (answer[i].description == "Earning Call Summary") {
                                    const pibData = eval(JSON.parse(JSON.stringify(answer[i].pibData)))
                                    setSummaryTranscript(pibData[0]['summary']);
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
                        } else {
                            console.log("Step not defined")
                        }
                    }
                )
                setIsLoading(false);
            }
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
            // if (selectedPromptTypeItemGpt?.key == "custom")
            // {
            //     promptTemplate = answersGpt[0][0]
            //     setPromptTemplateGpt(answersGpt[0][0]);
            // }

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
                    useInternet:useInternet
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
    const startOrStopSynthesis = async (answerType:string, url: string | null, index: number) => {
    };
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
    const onPromptTemplateChangeGpt = (_ev?: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        setPromptTemplateGpt(newValue || "");
    };
    const onTemperatureChangeGpt = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTemperatureGpt(parseInt(newValue || "0.3"));
    };
    const onTokenLengthChangeGpt = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTokenLengthGpt(parseInt(newValue || "500"));
    };
    const onEmbeddingChangeGpt = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItemGpt(item);
    };
    const onDeploymentTypeChangeGpt = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedDeploymentTypeGpt(item);
    };
    const onPromptTypeChangeGpt = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        clearChatGpt()
        setSelectedPromptTypeItemGpt(item);
        updatePromptGpt(String(item?.key));
    };
    const onUseInternetChanged = (ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean): void => {
        setUseInternet(!!checked);
    };
    const onTabChange = (item?: PivotItem | undefined, ev?: React.MouseEvent<HTMLElement, MouseEvent> | undefined): void => {
        if (item?.props.headerText === "Chat Pib") {
            clearChat()
            setSelectedDoc(docOptions[0])
            getCosmosSession(docOptions[0]?.key, String(symbol))
        } 
        if (item?.props.headerText === "Chat Gpt") {
            getCosmosSession("chatgpt", "cogsearchvs")
        } 
    };
    useEffect(() => {
        if (window.location.hostname != "localhost") {
            getUserInfoList();
            setShowAuthMessage(true)
        } else
            setShowAuthMessage(false)

        
        setSelectedExchange(exchangeOptions[0])
        setSelectedCompany(amexTickers[0]);
        setSelectedDoc(docOptions[0]);
        
        setSelectedEmbeddingItemGpt(embeddingGptOptions[0])
        setSelectedDeploymentTypeGpt(deploymentTypeGptOptions[0])
        setSelectedPromptTypeItemGpt(promptTypeGptOptions[0])
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
                <Pivot aria-label="Pib" onLinkClick={onTabChange}>
                    <PivotItem
                        headerText="Profile & Bio"
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
                                        {/* <Downshift
                                            onStateChange={({ inputValue }) => {
                                                console.log(inputValue)
                                            }}
                                            selectedItem={selectedCompany}
                                            onChange={selection => alert(`You selected ${selection}`)}
                                            >
                                            {({
                                                getInputProps,
                                                getItemProps,
                                                getLabelProps,
                                                isOpen,
                                                inputValue,
                                                highlightedIndex,
                                                selectedItem
                                            }) => (
                                                <div>
                                                <label {...getLabelProps()}>Select a Company</label>
                                                <input {...getInputProps()} />
                                                {isOpen ? (
                                                    <div>
                                                    {nasdaqTickers
                                                        .filter(i => !inputValue || i.text.includes(inputValue))
                                                        .map((item, index) => (
                                                        <div
                                                            {...getItemProps({
                                                            key: item.text,
                                                            index,
                                                            item,
                                                            style: {
                                                                backgroundColor:
                                                                highlightedIndex === index
                                                                    ? "lightgray"
                                                                    : "white",
                                                                fontWeight:
                                                                selectedItem === item ? "bold" : "normal"
                                                            }
                                                            })}
                                                        >
                                                            {item.text}
                                                        </div>
                                                        ))}
                                                    </div>
                                                ) : null}
                                                </div>
                                            )}
                                        </Downshift> */}

                                        <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} required={true} 
                                            errorMessage={!missingSymbol ? '' : "Symbol is required for PIB Functionality"}/>
                                        &nbsp;
                                        <PrimaryButton text="Get Profile & Bio" onClick={() => processPib("1")} disabled={isLoading} />
                                        <PrimaryButton text="ReProcess Get Profile & Bio" onClick={() => processPib("1")} disabled={true} />
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
                        headerText="Earning Calls"
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
                                              </p>
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
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Process Earning Calls" onClick={() => processPib("2")} />
                                        <PrimaryButton text="ReProcess Earning Calls" onClick={() => processPib("2")} disabled={true} />
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
                                                <TextField   
                                                    value={latestTranscript} disabled={true}
                                                    style={{ resize: 'none', width: '1000px', height: '500px' }}
                                                    multiline/>
                                            </Stack.Item>
                                            <br/>
                                            <Stack.Item grow={2} styles={stackItemStyles}>
                                                <Label>Earning Call Summary</Label>
                                                &nbsp; 
                                                <TextField  
                                                    value={summaryTranscript} disabled={true}
                                                    style={{ resize: 'none', width: '1000px', height: '300px' }}
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
                        headerText="Press Releases"
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
                                        <PrimaryButton text="Fetch Press Releases" onClick={() => processPib("3")} />
                                        <PrimaryButton text="ReProcess Press Releases" onClick={() => processPib("3")} disabled={true} />
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
                        headerText="SEC Filings"
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
                                        <PrimaryButton text="Crawl SEC Data" onClick={() => processPib("4")} />
                                        <PrimaryButton text="ReProcess SEC Data" onClick={() => processPib("4")} disabled={true} />
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
                        headerText="Private Data"
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
                                        <PrimaryButton text="Recommendations" onClick={() => processPib("5")} />
                                        <PrimaryButton text="ReProcess Recommendations" onClick={() => processPib("5")} disabled={true} />
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
                        headerText="News and Sentiment"
                        headerButtonProps={{
                        'data-order': 6,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 6 : </b> 
                                              This step focuses on pulling the <b>Private or Public</b> data that in form of getting the latest news about the company.
                                              Moreover it also shows the latest sentiment from twitter and other about the company in the form of a visual.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Get News & Sentiment" onClick={() => processPib("6")} />
                                        <PrimaryButton text="ReProcess News & Sentiment" onClick={() => processPib("6")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                        <div>
                                            <br/>
                                            {/* {
                                                stockNews && stockNews.length > 0 ? (
                                                    <MediaCard 
                                                        cardData={stockNews}/>
                                                ) : stockNews && stockNews.length === 0 ? "No data available" : ''
                                            } */}
                                        
                                            <DetailsList
                                                compact={true}
                                                items={stockNews || []}
                                                columns={stockNewsColumns}
                                                onRenderItemColumn={stockNewsRenderColumn}
                                                selectionMode={SelectionMode.none}
                                                getKey={(item: any) => item.key}
                                                selectionPreservedOnEmptyClick={true}
                                                layoutMode={DetailsListLayoutMode.justified}
                                                ariaLabelForSelectionColumn="Toggle selection"
                                                checkButtonAriaLabel="select row"
                                                />
                                            <br/>
                                            {
                                                socialSentiment ? (
                                                    <div>
                                                        <LineChart
                                                            culture={window.navigator.language}
                                                            data={socialSentiment}
                                                            legendsOverflowText={'Overflow Items'}
                                                            yMinValue={0}
                                                            yMaxValue={1}
                                                            height={300}
                                                            width={700}
                                                            margins={lineMargins}
                                                            xAxisTickCount={10}
                                                            allowMultipleShapesForPoints={false}
                                                            enablePerfOptimization={true}
                                                        />
                                                    </div>
                                                ) : null
                                            }
                                            

                                        </div>
                                    )}
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Financials"
                        headerButtonProps={{
                        'data-order': 7,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Step 7 : </b> 
                                              This step focuses on pulling the <b>Private or Public</b> financial data and showing the graphical charts for the same.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Show Financial Data" onClick={() => processPib("7")} />
                                        <PrimaryButton text="ReProcess Financial Data" onClick={() => processPib("7")} disabled={true} />
                                    </Stack.Item>
                                    {isLoading ? (
                                        <Stack.Item grow={2} styles={stackItemStyles}>
                                            <Spinner label="Processing..." ariaLive="assertive" labelPosition="right" />
                                        </Stack.Item>
                                        ) : (
                                        <div>
                                            <br/>
                                            {
                                                incomeStatement && cashFlow ? (
                                                    <div style={{width:'100%', height: 500}}>
                                                        <GroupedVerticalBarChart
                                                            chartTitle="Income Statement"
                                                            data={incomeStatement}
                                                            yAxisTickCount={5}
                                                            barwidth={23}
                                                        />
                                                        <GroupedVerticalBarChart
                                                            chartTitle="Cash Flow"
                                                            data={cashFlow}
                                                            yAxisTickCount={5}
                                                            barwidth={23}
                                                        />
                                                    </div>
                                                ) : null
                                            }
                                        </div>
                                    )}
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Summary"
                        headerButtonProps={{
                        'data-order': 8,
                        }}
                    >
                            <Stack enableScopedSelectors tokens={outerStackTokens}>
                                <Stack enableScopedSelectors styles={stackItemStyles} tokens={innerStackTokens}>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        <div className={styles.example}>
                                            <p><b>Summary : </b> 
                                              Final step in the PIB generation, this step for now is generating the PowerPoint presentation using the Open Office XML.  With the OOXML 
                                              based presentation they are compatible with the PowerPoint, Apple Keynote and other applications.
                                            </p>
                                        </div>
                                    </Stack.Item>
                                    <Stack.Item grow={2} styles={stackItemStyles}>
                                        &nbsp;
                                         <Label>Symbol :</Label>
                                        &nbsp;
                                        <TextField onChange={onSymbolChange}  value={symbol} disabled={true}/>
                                        &nbsp;
                                        <PrimaryButton text="Generate Presentation" onClick={() => generatePresentation()} />
                                    </Stack.Item>
                                </Stack>
                            </Stack>
                    </PivotItem>
                    <PivotItem
                        headerText="Chat Pib"
                        headerButtonProps={{
                        'data-order': 10,
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
                    <PivotItem
                        headerText="Chat Gpt"
                        headerButtonProps={{
                        'data-order': 11,
                        }}
                    >
                        <div className={styles.root}>
                            <br/>
                            <div className={styles.commandsContainer}>
                                <ClearChatButton className={styles.commandButton} onClick={clearChatGpt}  text="Clear chat" disabled={!lastQuestionRefGpt.current || isLoading} />
                                <SettingsButton className={styles.commandButton} onClick={() => setIsConfigPanelOpenGpt(!isConfigPanelOpenGpt)} />
                                <Checkbox label="Internet Search" checked={useInternet} onChange={onUseInternetChanged} />
                            </div>
                            <div className={styles.commandsContainer}>
                                <SessionButton className={styles.commandButton} onClick={clearChatGpt} />
                                <ClearChatButton className={styles.commandButton} onClick={deleteSessionGpt}  text="Delete Session" disabled={false} />
                                <RenameButton className={styles.commandButton}  onClick={renameSessionGpt}  text="Rename Session"/>
                                <TextField className={styles.commandButton} value={sessionNameGpt} onChange={onSessionNameChangeGpt}
                                    styles={{root: {width: '200px'}}} />
                            </div>
                            {/* <div className={styles.chatRoot}> */}
                            <Stack horizontal className={styles.chatRoot}>
                                {detailsListGpt}
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
                                        options={embeddingGptOptions}
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
                                            options={deploymentTypeGptOptions}
                                            disabled={((selectedEmbeddingItemGpt?.key == "openai" ? true : false))}
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
            </div>
            )}
        </div>
    );
};

export default Pib;

