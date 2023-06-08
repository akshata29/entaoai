import { useRef, useState, useEffect } from "react";
import { TextField, Stack, Spinner, IStackStyles, IStackTokens } from "@fluentui/react";
import { PrimaryButton } from "@fluentui/react";
import { githubLight } from '@uiw/codemirror-theme-github';
import { Label } from '@fluentui/react/lib/Label';
import { Pivot, PivotItem } from '@fluentui/react';

import styles from "./DeveloperTools.module.css";
import { Dropdown, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';
import { QuestionInput } from "../../components/QuestionInput";
import { Answer, AnswerError } from "../../components/Answer";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";
import { ClearChatButton } from "../../components/ClearChatButton";

import { convertCode, AskResponse, getSpeechApi, promptGuru, summarizer, AskRequest, Approaches } from "../../api";
import { ExampleList, ExampleModel } from "../../components/Example";
import { IStackItemStyles } from '@fluentui/react/lib/Stack';

import { StreamLanguage } from '@codemirror/language';
import { go } from '@codemirror/legacy-modes/mode/go';
import CodeMirror from '@uiw/react-codemirror';

var audio = new Audio();

const stackStyles: IStackStyles = {
    root: {
      //background: DefaultPalette.white,
    },
};

const itemStyles: React.CSSProperties = {
    alignItems: 'center',
    //background: DefaultPalette.white,
    //color: DefaultPalette.white,
    display: 'flex',
    justifyContent: 'center',
};

const stackTokens: IStackTokens = { childrenGap: 5 };

const DeveloperTools = () => {
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);

    const [isLoading, setIsLoading] = useState<boolean>(false);

    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [summary, setSummary] = useState<string>();
    const [promptSummary, setPromptSummary] = useState<string>();
    const [qa, setQa] = useState<string>('');
    const [exampleLoading, setExampleLoading] = useState(false)
  
    const [inputLanguage, setInputLanguage] = useState<string>('JavaScript');
    const [outputLanguage, setOutputLanguage] = useState<string>('Python');
    const [inputCode, setInputCode] = useState<string>('');
    const [outputCode, setOutputCode] = useState<string>('');
    const [hasTranslated, setHasTranslated] = useState<boolean>(false);
    const [translateError, setTranslateError] = useState(false)
    const [translateText, setTranslateText] = useState('');
    const lastQuestionRef = useRef<string>("");
    const [error, setError] = useState<unknown>();
    const [answer, setAnswer] = useState<[AskResponse, string | null]>();
    const [exampleList, setExampleList] = useState<ExampleModel[]>([{text:'', value: ''}]);
    const [gptPrompt, setGptPrompt] = useState('');
    const [gptSummary, setGptSummary] = useState('');


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

    const [selectedModelItem, setSelectedModelItem] = useState<IDropdownOption>();
    const modelOptions = [
        {
          key: 'gpt35',
          text: 'GPT 3.5'
        },
        {
          key: 'gpt4',
          text: 'GPT 4'
        }
    ]

    const [selectedInputLangItem, setSelectedInputLangItem] = useState<IDropdownOption>();
    const [selectedOutputLangItem, setSelectedOutputLangItem] = useState<IDropdownOption>();
    const languagesOptions = [
        { key: 'Pascal', text: 'Pascal' },
        { key: 'JavaScript', text: 'JavaScript' },
        { key: 'TypeScript', text: 'TypeScript' },
        { key: 'Python', text: 'Python' },
        { key: 'TSX', text: 'TSX' },
        { key: 'JSX', text: 'JSX' },
        { key: 'Vue', text: 'Vue' },
        { key: 'Go', text: 'Go' },
        { key: 'C', text: 'C' },
        { key: 'C++', text: 'C++' },
        { key: 'Java', text: 'Java' },
        { key: 'C#', text: 'C#' },
        { key: 'Visual Basic .NET', text: 'Visual Basic .NET' },
        { key: 'SQL', text: 'SQL' },
        { key: 'Assembly Language', text: 'Assembly Language' },
        { key: 'PHP', text: 'PHP' },
        { key: 'Ruby', text: 'Ruby' },
        { key: 'Swift', text: 'Swift' },
        { key: 'SwiftUI', text: 'SwiftUI' },
        { key: 'Kotlin', text: 'Kotlin' },
        { key: 'R', text: 'R' },
        { key: 'Objective-C', text: 'Objective-C' },
        { key: 'Perl', text: 'Perl' },
        { key: 'SAS', text: 'SAS' },
        { key: 'Scala', text: 'Scala' },
        { key: 'Dart', text: 'Dart' },
        { key: 'Rust', text: 'Rust' },
        { key: 'Haskell', text: 'Haskell' },
        { key: 'Lua', text: 'Lua' },
        { key: 'Groovy', text: 'Groovy' },
        { key: 'Elixir', text: 'Elixir' },
        { key: 'Clojure', text: 'Clojure' },
        { key: 'Lisp', text: 'Lisp' },
        { key: 'Julia', text: 'Julia' },
        { key: 'Matlab', text: 'Matlab' },
        { key: 'Fortran', text: 'Fortran' },
        { key: 'COBOL', text: 'COBOL' },
        { key: 'Bash', text: 'Bash' },
        { key: 'Powershell', text: 'Powershell' },
        { key: 'PL/SQL', text: 'PL/SQL' },
        { key: 'CSS', text: 'CSS' },
        { key: 'Racket', text: 'Racket' },
        { key: 'HTML', text: 'HTML' },
        { key: 'NoSQL', text: 'NoSQL' },
        { key: 'Natural Language', text: 'Natural Language' },
        { key: 'CoffeeScript', text: 'CoffeeScript' },
    ];

    const outerStackTokens: IStackTokens = { childrenGap: 5 };
    const innerStackTokens: IStackTokens = {
      childrenGap: 5,
      padding: 10,
    };

    const stackItemStyles: IStackItemStyles = {
    root: {
        alignItems: 'left',
        display: 'flex',
        justifyContent: 'left',
    },
    };

    const documentSummaryAndQa = async () => {
        const sampleQuestion = []
        const  questionList = [] 
        questionList.push("Act as a Linux Terminal")
        questionList.push("Act as an English Translator and Improver")
        questionList.push("Act as position Interviewer")
        questionList.push("Act as a JavaScript Console")
        questionList.push("Act as a Motivational Coach")
        questionList.push("Act as a Motivational Speaker")
        questionList.push("Act as a Personal Trainer")
        questionList.push("Act as a Real Estate Agent")
        questionList.push("Act As A Financial Analyst")
        questionList.push("Act as a SQL terminal")
        questionList.push("Act as a Python interpreter")
        questionList.push("Act as a Legal Advisor")
        questionList.push("Act as a Machine Learning Engineer")
        questionList.push("Act as a Time Travel Guide")
        questionList.push("Act as a ChatGPT prompt generator")
        questionList.push("Act as a Wikipedia page")

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

        const summary = "This use-case demostrates using LLM to generate Prompt for a given question/ask so that you can use the generated prompt to use for your scenario  "
        setPromptSummary(summary)
        setSummary("This sample demostrate converting your code from one language to another")

    }

    const onShowCitation = (citation: string) => {
    };
    
    const onToggleTab = (tab: AnalysisPanelTabs) => {
    };

    const gptCompletion = async () => {
        const requestText = JSON.stringify(gptPrompt)
    
        setGptSummary('')
    
        const request: AskRequest = {
            question: '',
            approach: Approaches.RetrieveThenRead,
            overrides: {
                temperature: 0,
                chainType: "map_reduce",
                tokenLength: 500,
            }
        };

        await summarizer(request, requestText, 'custom', '', 'inline', 
          "map_reduce", String(selectedEmbeddingItem?.key)).then((response) => {
            setGptSummary(response)
          }).catch((error) => {
            console.log(error)
            setGptSummary(error)
        }
        )
    }

    const handleTranslate = async () => {
        const maxCodeLength = selectedModelItem?.key === 'gpt35' ? 6000 : 12000;
        
        if (inputLanguage === outputLanguage) {
            setTranslateError(true);
            setTranslateText('Please select different languages.');
            return;
        }
    
        if (!inputCode) {
            setTranslateError(true);
            setTranslateText('Please enter some code.');
            return;
        }
    
        if (inputCode.length > maxCodeLength) {
            setTranslateError(true);
            setTranslateText(
            `Please enter code less than ${maxCodeLength} characters. You are currently at ${inputCode.length} characters.`,
            );
          return;
        }
    
        setIsLoading(true);
        setOutputCode('');
        setTranslateText('')
        setTranslateError(false)
        
        await convertCode(inputLanguage, outputLanguage, inputCode, selectedModelItem?.key as string, selectedEmbeddingItem?.key as string)
          .then((response:string) => {
            if (response.length > 0) {
                setOutputCode(response)
                setIsLoading(false)
                setTranslateText("Completed Successfully.")
            }
            else {
                setTranslateText(response)
            }
            setIsLoading(false)
          })
          .catch((error : string) => {
            setTranslateError(true)
            setTranslateText(error)
            setIsLoading(false)
        })
        setIsLoading(false);
        setHasTranslated(true);
    };

    const startSynthesis = async (answerType: string, url: string | null) => {
        if(isSpeaking) {
            audio.pause();
            setIsSpeaking(false);
        }

        if(url === null) {
            let speechAnswer;
            if (answerType == "Answer")
                speechAnswer = answer && answer[0].answer;

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

    const promptChange = (ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        setGptPrompt(newValue || '')
    }
    const makePromptApiRequest = async (question: string) => {
        lastQuestionRef.current = question;

        error && setError(undefined);
        setIsLoading(true);

        try {
            const result = await promptGuru(question, selectedModelItem?.key as string, selectedEmbeddingItem?.key as string);
            //setAnswer(result);
            setAnswer([result, null]);
        } catch (e) {
            setError(e);
        } finally {
            setIsLoading(false);
        }
    };

    const onExampleClicked = (example: string) => {
        makePromptApiRequest(example);
    };

    const clearChat = () => {
    };

    useEffect(() => {
        documentSummaryAndQa()
        setSelectedEmbeddingItem(embeddingOptions[0])
        setSelectedModelItem(modelOptions[0])
        setIsLoading(false)
    }, [])

    const onEmbeddingChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedEmbeddingItem(item);
    };

    const onModelChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedModelItem(item);
    };

    const onInputLangChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedInputLangItem(item);
        setInputLanguage(item?.key as string);
        setHasTranslated(false);
        setInputCode('');
        setOutputCode('');
    };
  
    const onOutputLangChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedOutputLangItem(item);
        setOutputLanguage(item?.key as string);
        setOutputCode('');
    };

    return (

        <div className={styles.root}>
            <div className={styles.developerToolsContainer}>
            <Pivot aria-label="Chat">
                    <PivotItem
                        headerText="Code Translation"
                        headerButtonProps={{
                        'data-order': 1,
                        }}
                    >
                        <div className={styles.developerToolsTopSection}>
                            {/* <div className={styles.commandsContainer}>
                                <ClearChatButton className={styles.settingsButton} onClick={clearChat} disabled={!lastQuestionRef.current || isLoading} />
                                <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                            </div> */}
                            <br/>
                            <div className={styles.commandsContainer}>
                            &nbsp;&nbsp;<Label>LLM</Label>
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
                                &nbsp;
                                <Label>Model</Label>
                                &nbsp;
                                <Dropdown
                                    selectedKey={selectedModelItem ? selectedModelItem.key : undefined}
                                    onChange={onModelChange}
                                    defaultSelectedKey="gpt35"
                                    placeholder="Select an Model"
                                    options={modelOptions}
                                    disabled={false}
                                    styles={dropdownStyles}
                                />                               
                            </div>
                            <br/>
                            <h1 className={styles.developerToolsTitle}>Code Conversion</h1>
                            <div className={styles.example}>
                                <p className={styles.exampleText}><b>Document Summary</b> : {summary}</p>
                            </div>
                            <br/>
                        </div>
                        <div className={styles.developerToolsBottomSection}>
                            <Stack enableScopedSelectors  tokens={innerStackTokens}>
                                <Stack.Item grow styles={stackItemStyles}>
                                    <div className={styles.commandsContainer}>
                                        <Label>Input Language: </Label>
                                        &nbsp;
                                        <Dropdown
                                            selectedKey={selectedInputLangItem ? selectedInputLangItem.key : undefined}
                                            onChange={onInputLangChange}
                                            defaultSelectedKey="JavaScript"
                                            placeholder="Select an Language"
                                            options={languagesOptions}
                                            disabled={false}
                                            styles={dropdownStyles}
                                        />
                                        &nbsp;
                                        <Label>Output Language: </Label>
                                        &nbsp;
                                        <Dropdown
                                            selectedKey={selectedOutputLangItem ? selectedOutputLangItem.key : undefined}
                                            onChange={onOutputLangChange}
                                            defaultSelectedKey="Python"
                                            placeholder="Select an Language"
                                            options={languagesOptions}
                                            disabled={false}
                                            styles={dropdownStyles}
                                        />
                                        &nbsp;
                                        <PrimaryButton text={isLoading ? 'Translating...' : 'Translate'}
                                        disabled={isLoading} onClick={handleTranslate} />
                                    </div>
                                    </Stack.Item>
                                    <Stack.Item grow styles={stackItemStyles}>
                                        <TextField disabled={true} label={translateError ? '' : translateText} errorMessage={!translateError ? '' : translateText} />
                                    </Stack.Item>
                                    <Stack.Item grow styles={stackItemStyles}>
                                    <div className={styles.commandsContainer}>
                                        {inputLanguage === 'Natural Language' ? (
                                                <textarea
                                                style={{ resize: 'none' }}
                                                value={inputCode}
                                                onChange={(e) => {
                                                    setInputCode(e.target.value);
                                                    setHasTranslated(false);
                                                    }}
                                                disabled={!isLoading}
                                            />
                                        ) : (
                                            <CodeMirror
                                                editable={!isLoading}
                                                value={inputCode}
                                                minHeight="750px"
                                                width="550px"
                                                theme={githubLight}
                                                extensions={[StreamLanguage.define(go)]}
                                                onChange={(value) => {
                                                    setInputCode(value);
                                                    setHasTranslated(false);
                                                }}
                                            />
                                        )}
                                        &nbsp;&nbsp;&nbsp;
                                        {outputLanguage === 'Natural Language' ? (
                                            <textarea
                                                style={{ resize: 'none' }}
                                                value={outputCode}
                                                disabled={!isLoading}
                                            />
                                        ) : (
                                            <CodeMirror
                                                value={outputCode}
                                                theme={githubLight}
                                                minHeight="750px"
                                                width="550px"
                                            />
                                        )}

                                    </div>
                                </Stack.Item>
                            </Stack>
                        </div>
                    </PivotItem>
                    <PivotItem
                        headerText="Prompt Guru"
                        headerButtonProps={{
                        'data-order': 2,
                        }}
                    >
                        <div className={styles.developerToolsTopSection}>
                            <br/>
                            <div className={styles.commandsContainer}>
                                &nbsp;&nbsp;<Label>LLM</Label>
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
                                &nbsp;
                                <Label>Model</Label>
                                &nbsp;
                                <Dropdown
                                    selectedKey={selectedModelItem ? selectedModelItem.key : undefined}
                                    onChange={onModelChange}
                                    defaultSelectedKey="gpt35"
                                    placeholder="Select an Model"
                                    options={modelOptions}
                                    disabled={false}
                                    styles={dropdownStyles}
                                />                               
                            </div>
                            <br/>
                            <h1 className={styles.developerToolsTitle}>Prompt Guru</h1>
                            <div className={styles.example}>
                                <p className={styles.exampleText}><b>Document Summary </b> : {promptSummary}
                                </p>
                            </div>
                            <br/>
                            <div className={styles.developerToolsQuestionInput}>
                                <QuestionInput
                                    placeholder="Ask me anything"
                                    updateQuestion={lastQuestionRef.current}
                                    disabled={isLoading}
                                    onSend={question => makePromptApiRequest(question)}
                                />
                            </div>
                            {!answer && (<h4 className={styles.developerToolsEmptyStateSubtitle}>Ask anything or try from following example</h4>)}
                            {exampleLoading ? <div><span>Please wait, Generating Sample Question</span><Spinner/></div> : null}
                            <ExampleList onExampleClicked={onExampleClicked}
                            EXAMPLES={
                                exampleList
                            } />
                        </div>
                        <div className={styles.developerToolsBottomSection}>
                            <div className={styles.developerToolsBottomSection}>
                                {isLoading && <Spinner label="Generating answer" />}
                                {!isLoading && answer && !error && (
                                    <div>
                                        <div className={styles.developerToolsAnswerContainer}>
                                            <Stack horizontal horizontalAlign="space-between">
                                                <Answer
                                                    answer={answer[0]}
                                                    isSpeaking = {isSpeaking}
                                                    onCitationClicked={x => onShowCitation(x)}
                                                    onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab)}
                                                    onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab)}
                                                    onFollowupQuestionClicked={q => makePromptApiRequest(q)}
                                                    onSpeechSynthesisClicked={() => isSpeaking? stopSynthesis(): startSynthesis("Answer", answer[1])}
                                                />
                                            </Stack>                               
                                        </div>
                                    </div>
                                )}
                                {error ? (
                                    <div className={styles.developerToolsAnswerContainer}>
                                        <AnswerError error={error.toString()} onRetry={() => makePromptApiRequest(lastQuestionRef.current)} />
                                    </div>
                                ) : null}
                            </div>
                        </div>
                    </PivotItem>
                    <PivotItem
                        headerText="OpenAI Playground"
                        headerButtonProps={{
                        'data-order': 3,
                        }}
                    >
                        <div className={styles.developerToolsTopSection}>
                            <br/>
                            <div className={styles.commandsContainer}>
                                &nbsp;&nbsp;<Label>LLM</Label>
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
                                &nbsp;
                                <Label>Model</Label>
                                &nbsp;
                                <Dropdown
                                    selectedKey={selectedModelItem ? selectedModelItem.key : undefined}
                                    onChange={onModelChange}
                                    defaultSelectedKey="gpt35"
                                    placeholder="Select an Model"
                                    options={modelOptions}
                                    disabled={false}
                                    styles={dropdownStyles}
                                />                               
                            </div>
                            <br/>
                            <h1 className={styles.developerToolsTitle}>OpenAI Playground</h1>
                            <br/>
                            <Stack enableScopedSelectors tokens={stackTokens}>
                                <Stack enableScopedSelectors horizontal horizontalAlign="start" styles={stackStyles}>
                                    <span style={itemStyles}>
                                        <TextField 
                                            multiline
                                            styles={{root: {width: '600px', height: '500px'}}}
                                            label="Prompt"
                                            value={gptPrompt}
                                            rows={25}
                                            onChange={promptChange}
                                        />
                                        {/* <textarea
                                            style={{ resize: 'none', width: '100%', height: '500px' }}
                                            value={gptPrompt}
                                            onChange={(e) => {
                                                setGptPrompt(e.target.value);
                                                }}
                                        /> */}
                                    </span>
                                    <span style={itemStyles}>
                                        &nbsp;&nbsp;&nbsp;&nbsp;
                                    </span>
                                    <span style={itemStyles}>
                                        <TextField 
                                            multiline
                                            styles={{root: {width: '700px', height: '500px'}}}
                                            label="OpenAI Summary"
                                            readOnly
                                            value={gptSummary}
                                            rows={25}
                                        />
                                        {/* <textarea
                                            style={{ resize: 'none', width: '100%', height: '500px' }}
                                            value={gptSummary}
                                        /> */}
                                    </span>
                                </Stack>
                            </Stack>
                            <PrimaryButton text={isLoading ? 'Completion...' : 'Completion'}
                                        disabled={isLoading} onClick={gptCompletion} />
                        </div>
                    </PivotItem>
                </Pivot>
            </div>
        </div>
    );
};

export default DeveloperTools;

