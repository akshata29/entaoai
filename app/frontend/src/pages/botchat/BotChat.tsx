import React, {  useState, memo, useMemo, useEffect, useCallback } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, Spinner, List } from "@fluentui/react";
import { SparkleFilled, BarcodeScanner24Filled } from "@fluentui/react-icons";
import ReactWebChat, { createStore, createDirectLine } from 'botframework-webchat';

import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import styles from "./BotChat.module.css";
import { Label } from '@fluentui/react/lib/Label';
import { ExampleList, ExampleModel } from "../../components/Example";

import { refreshIndex, AskResponse, ChatRequest, ChatTurn } from "../../api";
import { ClearChatButton } from "../../components/ClearChatButton";

//const directLine = useMemo(() => createDirectLine({ token: 'xPuhSjJIjLg.Tn4pvBAvKuuGv3RQMCoh2-HtyRxUniqErFbtsbQpJQs' }), []);
//const directLine = createDirectLine({ token: 'xPuhSjJIjLg.Tn4pvBAvKuuGv3RQMCoh2-HtyRxUniqErFbtsbQpJQs' });

const BotChat = () => {
    const [selectedIndex, setSelectedIndex] = useState<string>();
    const [indexMapping, setIndexMapping] = useState<{ key: string; iType: string; summary:string; qa:string;  }[]>();
    const [summary, setSummary] = useState<string>();
    const [userId, setUserId] = useState<string>();
    const [qa, setQa] = useState<string>('');
    const [options, setOptions] = useState<any>([])
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [directLineToken, setDirectLineToken] = useState<any>(undefined)
    const [directLine, setDirectLine] = useState<any>();

    useEffect(() => {
   
        setDirectLine(createDirectLine({ token: 'xPuhSjJIjLg.Tn4pvBAvKuuGv3RQMCoh2-HtyRxUniqErFbtsbQpJQs' }));
    }, [setDirectLine]);

    const fetchToken = async () => {
        const res = await fetch('https://directline.botframework.com/v3/directline/tokens/generate', { 
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' +  'xPuhSjJIjLg.Tn4pvBAvKuuGv3RQMCoh2-HtyRxUniqErFbtsbQpJQs',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user: {
                  id: userId
                }
            })
         });
        const { token } = await res.json();
        console.log(token)
        setDirectLineToken(token)
    };
    
    const [selectedItem, setSelectedItem] = useState<IDropdownOption>();
    
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
                //setExampleList(generatedExamples)
                //setExampleLoading(false)
            }
        }
        setIndexMapping(uniqIndexType)
    }

    

    useEffect(() => {
        setOptions([])
        refreshBlob()
        setDirectLine(createDirectLine({ token: 'xPuhSjJIjLg.Tn4pvBAvKuuGv3RQMCoh2-HtyRxUniqErFbtsbQpJQs' }));
    }, [])

    const clearChat = () => {
    };

    const onChange = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setSelectedItem(item);
        clearChat();
        const r = (Math.random() + 1).toString(36).substring(7);
        setUserId(r)

        const defaultKey = item?.key
        let indexType = 'pinecone'

        indexMapping?.findIndex((item) => {
            if (item.key == defaultKey) {
                indexType = item.iType
                setSelectedIndex(item.iType)
                setSummary(item.summary)
                setQa(item.qa)

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
                //setExampleList(generatedExamples)
                //setExampleLoading(false)
            }
        })
    };

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
                    &nbsp;
                    <Label className={styles.commandsContainer}>Index Type : {selectedIndex}</Label>
                </div>
            </div>
            <div className={styles.container}>
                <div className={styles.commandsContainer}>
                    <ClearChatButton className={styles.commandButton} onClick={clearChat} text="Clear chat" />
                </div>
                <div className={styles.chatRoot}>
                    <div className={styles.chatContainer}>
                        {!!directLine && 
                        <ReactWebChat directLine={directLine} userID={userId} 
                            locale="en-Us"
                            //store={store}
                            styleOptions={{
                                accent: '#348FFC',
                                typingAnimationHeight: 20,
                                typingAnimationWidth: 100,
                                backgroundColor: 'rgb(237, 237, 237)',
                                bubbleFromUserTextColor: '#fff',
                                bubbleFromUserBackground: '#348FFC',
                                bubbleFromUserBorderRadius: 5,
                                bubbleBorderRadius: 5,
                                suggestedActionBorderColor: '#348FFC',
                                suggestedActionBackground: '#348FFC',
                                suggestedActionTextColor: '#fff',
                                cardEmphasisBackgroundColor: 'Red',
                                suggestedActionBorderRadius: 5,
                                avatarSize: 30,
                                paddingRegular: 15,
                                rootHeight: '650px',
                                rootWidth: '80%',
                                hideScrollToEndButton: false,
                                sendBoxHeight: 50,
                                hideUploadButton: true,
                                hideSendBox: false,
                                botAvatarInitials: 'Bot',
                                userAvatarInitials: 'You'
                        }}/>
                        }
                        {/* <WebChat directLine={directLine} store={store}/> */}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default memo(BotChat);
