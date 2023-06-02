import { useState, useEffect, SetStateAction } from "react";
import { TextField, PrimaryButton, Label, DefaultPalette, Stack, IStackStyles, IStackTokens } from "@fluentui/react";
import { Checkbox,Panel, DefaultButton,  SpinButton } from "@fluentui/react";

import styles from "./Speech.module.css";
import { Dropdown, DropdownMenuItemType, IDropdownStyles, IDropdownOption } from '@fluentui/react/lib/Dropdown';

import { AskRequest, Approaches, getSpeechToken, textAnalytics, summarizer } from "../../api";

import { ResultReason } from 'microsoft-cognitiveservices-speech-sdk'
import * as speechsdk from 'microsoft-cognitiveservices-speech-sdk';
import { SettingsButton } from "../../components/SettingsButton/SettingsButton";
var recognizer: speechsdk.SpeechRecognizer

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

const Speech = () => {
    const dropdownStyles: Partial<IDropdownStyles> = { dropdown: { width: 300 } };
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [temperature, setTemperature] = useState<number>(0);
    const [tokenLength, setTokenLength] = useState<number>(1000);
    const [chainTypeOptions, setChainTypeOptions] = useState<any>([])
    const [selectedChain, setSelectedChain] = useState<IDropdownOption>();

    const bankingRaw = "Royal Human Bank, this is Linda speaking. \r\n Hi Linda. I was just at your Bridgeport branch and I think I left my Debit card in the ATM machine \r\n Okay. Do you have your Debit card number? \r\n Actually, I don’t. \r\n Okay, well do you have the checking account number associated with the Debit card? That I do have. Are you ready? I’ll give you what I’ve got. 765 456 789.  Okay. That’s 765 456 789.  \r\n Correct\r\n Okay and what is your name sir? \r\n It’s Robert Applebaum. That’s A-P-P-L-E-B-A-U-M. \r\n Okay. I have Robert Applebaum.\r\n Yes\r\n And what is your date of birth Robert? \r\n July 7th, 1974. \r\n Okay. And your phone number? \r\n It’s 610-265-1715. \r\n Okay Robert. I have just temporarily suspended your card. If it is in the machine, we will contact you and lift the suspension. \r\n Oh, thank you. \r\n Sure. Thank you. \r\n Goodbye\r\n Goodbye"
    const insuranceRaw = "Thank you for calling Contoso Insurance. My name is Ashish Talati How may I help you? \r\n I had an accident. I am calling to file a new claim\r\n Oh, I am so sorry to hear that.  Was anyone injured in the accident?\r\n No, nobody was injured. Kids were scared and there is some damage to the car but thankfully nobody suffered any injuries.\r\n That’s good to hear. Can I get your name please? \r\n My name is John Smith \r\n Can you please verify your data of birth?\r\n It is October 29th, 1984\r\n Let me pull up your information. Please hold on \r\n I see you live at 425 Michigan Ave in Chicago, IL. Is that correct?\r\n Yes\r\n Can you please verify your phone number in case we need to contact you?\r\n My phone number is 312-456-9876 \r\n I see you have multiple cars on the policy. Which car was involved in the accident?\r\n It was my Honda Accord\r\n Ok, where did the accident happen?\r\n It happened in the Walmart parking lot in the north side of Chicago. It was raining heavily and I guess the other car didn’t see my car when backing up.\r\n Ok, when did the accident happen? \r\n It happened on Sunday morning around 10am. I think it was September 12.\r\n Can you please describe the damage to your car? \r\n Yes, front of other person’s car hit my car’s bumper on the right side.\r\n Ok, let me create a new claim for this. Please hold on \r\n I have created a new claim for you. We will be contacting you for scheduling repairs to your car. Is there anything else I can help with?\r\n No, thank you for your help.\r\n My Pleasure.  You have a great day!"
    const bankingCcRaw = "Hello, how may I help you today? \r\n I really need help with my credit card, it's not working at all \r\n May I please have your first and last name \r\n sure it's John, J O H N, Doh, D O E \r\n Thank you Mr Doh, can you confirm the last four digits of your account number? \r\n Which number? Is that the card number or the number on my statement, I don't have a statement in front of me. \r\n It should be the last four digits printed on your credit card. \r\n Ok, let me get it, my wallet is in the other room.\nI have it now, the number is 4 3 2 1 \r\n Thank you again Mr Doh.\nIt looks like there is suspected fraud on your credit card. Can you confirm the last purchase you made? \r\n I tried to use it to book an Air Bee En Bee for my daughter. \r\n Can you confirm the charge amount? \r\n I don't know. it was about two thousand dollars for a stay in December in Florida. \r\n Ok I can confirm the amount now, our system detected it as fraud but since you have confirmed it we will mark it as approved. Please proceed with your booking. \r\n I hope I can get the same house. bookings were hard to find in that area. I'm going to try now.ok it looks like the booking went through thank you \r\n Is there anything else I can help you with? \r\n Yes, as a matter of fact. I want to order another card for my daughter to use. \r\n Sure, I can help you with that, can I have her first and last name? \r\n Jane, J A N E, Doh, D O E. \r\n What address can I mail the card to? \r\n You can mail it to the default address on Pine Wood Ave. \r\n Ok you can expect the card in 1 to 2 business days.Is there anything else? \r\n No thank you for your help."
    const bankingLoanRaw = "Good afternoon. This is Sam. Thank you for calling Contessa. How may I help? \r\n Hi there, my name is Mary. I'm currently living in Los Angeles, but I'm planning to move to Las Vegas and I would like to apply for a loan. \r\n OK, I see you're living in California. Let me make sure I understand you correctly. Uh, you'd like to apply for a loan even though you'll be moving soon, is that right? \r\n Yes, exactly. So I'm planning to relocate soon, but I would like to apply for the loan first so that I can purchase a new home once I move there. \r\n And are you planning to sell your current home?  \r\n Yes, I will be listing on the market soon and hopefully it'll sell quickly. That's why I'm applying for a loan now, so that I can purchase a new house in Nevada and close on it quickly as well once my current home sells.  \r\n I see. Um, would you mind holding for a moment while I take your information down?  \r\n Yeah, no problem. Thank you for your help. \r\n Alright. Thank you for your patience ma'am. May I have your first and last name please?  \r\n Yes, uh, my name is Mary Smith. Thank you. Miss Smith. May I have your current address, please?  \r\n Yes, so my address is 123 Main St. in Los Angeles, CA and the ZIP code is 90923.  \r\n Sorry, that was a 90 what? \r\n  90923.  \r\n 90923 on Main Street. Got it. Thank you. Uh, may I have your phone number as well please?  \r\n Uh, yes, my phone number is 504. 5292351  \r\n and then. \r\n  51. Got it. Uh and uh, do you have an e-mail address? Um, we I can associate with this application?  \r\n Uh, yes. So my e-mail address is mary.a.sm78@gmail.com.  \r\n Mary dot A was that a SN as in November or M as in Mike?  \r\n Uh M as in Mike?  \r\n Like 78, uh, got it right. Thank you, Miss Smith. Um, do you currently have any other loans? Uh yes. So I currently have two other loans through CONTOSO. Uh. So my first one is my car loan and then my other is my student loan.  \r\n Uh they total about 1400 per month combined and my interest rate is 8%.  \r\n I see. And you're currently paying those loans off monthly, is that right?  \r\n Yes, of course I do. OK, thank you. Umm, here's what I suggest we do. Uh, let me place you on a brief hold again so I can talk with one of my loan officers and get this started for you immediately. And in the meantime, would be great if you could take a few minutes and complete the remainder of the secure application online at www.contosoloans.com.  \r\n Yeah, that sounds good. I can go ahead and get started. Thank you for your help.  \r\n Thank you. "
    const insurancePharmRaw = "Hi. Thank you for calling Contoso pharmacy. Who am I speaking with today? \r\n Good afternoon. My name is Mary. I'm calling about a refill from my prescribed medications. I have been trying to get a hold of someone for weeks and was told that I would get a call back regarding my situation, but it's been weeks and no one's contacted me, so I thought I'd call. \r\n I understand your frustration, Mary. Can you tell me what exactly you're trying to accomplish? \r\n Yes, I'm trying to get a refill of my prescription drugs that the my doctor prescribed to me for cholesterol. \r\n OK, uh, certainly happy to check that for you. One moment please. \r\n I see here that you were on a generic form of Lipitor. Is that right? \r\n Uh, yes, I was taking the generic form of Lipitor. \r\n OK. Uh, so I see that your doctor stopped prescribing these drugs in 2021, actually. \r\n Ohh really? That doesn't sound right. I don't remember him cancelling my prescription. \r\n OK, uh, yeah, I'd be happy to check that for you. Uh, because sometimes there's a gap in the system and it just doesn't get reported. So let me take a look here. \r\n Just a moment. \r\n So I'm seeing here that your doctor had these drugs prescribed to you from 2012 through 2021. \r\n Oh, huh. I mean, I'm definitely supposed to be taking something else. Uh, would you check, please? \r\n OK. Yeah. According to the latest records provided by doctor's office, you're now on a different drug metformin. Would you like us to go ahead and fill that prescription for you for pick up form in 500 milligrams? \r\n Uh, yeah, yeah. Thank you so much. I'm almost out, so that'd be perfect. \r\n You're very welcome, Mary. Please let us know if there's anything else we can do for you today. \r\n OK. Thank you. "
    const insuranceHealthRaw = "Hello. Thank you for calling Contoso. Who am I speaking with today? \r\n Hi, my name is Mary Rondo. I'm trying to enroll myself with Contoso. \r\n Hi, Mary. Uh, are you calling because you need health insurance? \r\n Yes, yeah, I'm calling to sign up for insurance. \r\n Great. Uh, if you can answer a few questions, uh, we can get you signed up in the Jiffy. \r\n \r\n OK. So, uh, what's your full name? \r\n Uh, some Mary Beth Rondo last name is R like Romeo, O like ocean and like Nancy, DD like dog and O like ocean again. \r\n Randall got it. And what's the best callback number in case we get disconnected? \r\n I only have a cell phone so I can give you that. \r\n Yeah, that'll be fine.\r\n  Sure. So it's 234554 and then 9312. \r\n Here to confirm it's 2345549312. Yep, that's right. \r\n Excellent. Uh, let's get some additional information from your app for your application. \r\n Uh, do you have a job? Uh, yes, I am self-employed. \r\n OK, so then you have a Social Security number as well. \r\n I guess I do. \r\n OK. And what is your Social Security number please? \r\n Uh, sure. So it's 412. Uh 256789.\r\n Sorry, what was that A-25 or A225 you cut out for a bit? \r\n Uh, it's 22 so. 412, then another two, then five. \r\n Hey, thank you so much. And could I have your e-mail address please? \r\n Yeah, it's Mary rhondo@gmail.com, so myfirstandlastname@gmail.com. No periods, no dashes. \r\n Great. Uh, that is the last question. So let me take your information and I'll be able to get you signed up right away. Thank you for calling Contoso and I'll be able to get you signed up immediately. One of our agents will call you back in about 24 hours or so to confirm your application. \r\n That sounds great. Thank you. \r\n Absolutely. If you need anything else, please give us a call at 1-800-555-5564, ext. 123. Thank you very much for calling Contoso. \r\n Uh, actually, uh, sorry, one more question. \r\n Uh, yes, of course. \r\n I'm curious what I'd be getting a physical card as proof of coverage. \r\n So the default is a digital membership card, but we can send you a physical card if you prefer. \r\n Uh, yes. Could you please mail it to me when it's ready? I'd like to have it shipped to you for my address. \r\n Uh, yeah. \r\n Uh, so it's 2660 unit A on Maple Ave. SE Lansing, and then ZIP code is 48823. \r\n Absolutely. I've made a note on your file. \r\n Awesome. Thanks so much. You're very welcome. Thank you for calling Contoso and have a great day. "
    const insurancePrompt = "Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer\n3. Where the accident happened?\n4. How did the accident happen?\n5. What was the weather like when the accident happened?\n6. What is customer's phone number?\n7. Was the airbag deployed when accident happened?"
    const healthcarePrompt = "Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer\n3. What health condition was discussed? \n4. Was any medication mentioned in the conversation?\n5. Identify medical entities such as symptoms, medications, diagnosis from this conversaion."
    const bankingPrompt = "Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer"
    const capitalMarketsPrompt = "Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer"
    const generalPrompt = "Extract the following from the conversation:\n1. Main reason of the conversation\n2. Sentiment of the customer\n3. What are the action items and follow-ups?"
    const participantPrompt = "Extract list of call participants in list format from the following text"
    const summaryNotesPrompt = "Generate detailed call summary notes in list format from the following text"
    const followupPrompt = "Generate list of call follow up tasks from following text"
    const complexPrompt = "You must extract the following information from the phone conversation below: \n\n 1. Call reason (key: reason) \n 2. Cause of incident (key: cause) \n 3. Name of caller (key: caller) \n 4. Account number (key: account_id) \n 5. Follow-up Flag(key: followupind) \n 6. A short, yet detailed summary (key: summary) \n\n Make sure fields 1 to 4 are answered very short. Field 5 is a boolean flag which indicates whether the caller incident was resolved, 1 if follow up required, 0 if resolved.  Please answer in JSON machine-readable format, using the keys from above. Format the output as JSON object. Pretty print the JSON and make sure that is properly closed at the end."
    const pharmacyPrompt = "Provide list of medications, dose, and form discussed in the following text"
    const piiPrompt = "List of all PII and named entities and what is overall sentiment"
    const topicsPrompt = "Generate list of topics discussed from text"
    const [scenario, setScenario] = useState<IDropdownOption>();
    const [sentimentMining, setSentimentMining] = useState('')
    const [language, setLanguage] = useState<IDropdownOption>();
    const [languageExtractiveSummary, setLanguageExtractiveSummary] = useState('')
    const [languageAbstractiveSummary, setLanguageAbstractiveSummary] = useState('')
    const [languagePostCallSummary, setLanguagePostCallSummary] = useState('')
    const [gptSummary, setGptSummary] = useState('')
    const [gptDetails, setGptDetails] = useState('')
    const [gptPromptSummary, setGptPromptSummary] = useState<string>()
    const [promptDetails, setPromptDetails] = useState(
        "Extract the following from the conversation: \n 1. What is customer's name? \n 2. Which car was involved in the accident? \n 3. What are the action items and follow-ups?"
    )

    const chainType = [
      { key: 'stuff', text: 'Stuff'},
      { key: 'map_rerank', text: 'Map ReRank' },
      { key: 'map_reduce', text: 'Map Reduce' },
      { key: 'refine', text: 'Refine'},
    ]

    const [promptType, setPromptType] = useState<IDropdownOption>();
    const scenarioType = [
        { key: 'Insurance', text: 'Insurance' },
        { key: 'General', text: 'General'},
        { key: 'BankingRaw', text: 'Banking Script' },
        { key: 'BankingCcRaw', text: 'Banking CC Script' },
        { key: 'BankingLoanRaw', text: 'Banking Loan Script'},
        { key: 'InsuranceRaw', text: 'Insurance Script'},
        { key: 'InsurancePharmRaw', text: 'Insurance Pharmacy Script' },
        { key: 'InsuranceHealthRaw', text: 'Insurance Health Script' },
    ]

    const languages = [
      { key: 'en-US', text: 'English (USA)' },
      { key: 'en-GB', text: 'English (UK)' },
      { key: 'es-ES', text: 'Spanish (Spain)' },
      { key: 'es-MX', text: 'Spanish (Mexico)' },
      { key: 'fr-CA', text: 'French (Canada)' },
      { key: 'fr-FR', text: 'French (France)' },
      { key: 'it-IT', text: 'Italian (Italy)' },
      { key: 'ja-JP', text: 'Japanese (Japan)' },
      { key: 'da-DK', text: 'Danish (Denmark)' },
      { key: 'wuu-CN', text: 'Chinese (Wu, Simplified)' },
      { key: 'hi-IN', text: 'Hindi (India)' },
      { key: 'gu-IN', text: 'Gujarati (India)' },
      { key: 'te-IN', text: 'Telugu (India)' },
      { key: 'de-DE', text: 'German (Germany)' },
      { key: 'el-GR', text: 'Greek (Greece)' },
      { key: 'ar-EG', text: 'Arabic (Egypt)' },
      { key: 'el-GR', text: 'Greek (Greece)' },
      { key: 'ar-IL', text: 'Arabic (Israel)' },
      { key: 'ar-SA', text: 'Arabic (Saudi Arabia)' },
      { key: 'cs-CZ', text: 'Czech (Czechia)' },
      { key: 'ko-KR', text: 'Korean (Korea)' },
      { key: 'nl-NL', text: 'Dutch (Netherlands)' },
      { key: 'pt-BR', text: 'Portuguese (Brazil)' },
      { key: 'pt-PT', text: 'Portuguese (Portugal)' },
      { key: 'sv-SE', text: 'Swedish (Sweden)' },
      { key: 'he-IL', text: 'Hebrew (Israel)' },
  ]

    const promptTypes = [
        { key: 'summaryNotes', text: 'Summary Notes'},
        { key: 'participants', text: 'Participants List' },
        { key: 'followup', text: 'Followup' },
        { key: 'pii', text: 'PII & Entities'},
        { key: 'topics', text: 'Topics'},
        { key: 'pharmacy', text: 'Pharmacy' },
        { key: 'complex', text: 'Complex' },
        { key: 'custom', text: 'Custom'},
    ]

    const [speechToken, setSpeechToken] = useState('')
    const [speechText, setspeechText] = useState('Speak into your microphone to start conversation...')
    const [speechRegion, setSpeechRegion] = useState('')
    const [nlpText, setNlpText] = useState('')
    const nlpArray: String[] = []


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
    
    const setScenarios = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item?.key == 'BankingRaw') {
            setspeechText(bankingRaw)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
            setPromptDetails(bankingPrompt)
          } else if (item?.key == 'BankingCcRaw') {
            setspeechText(bankingCcRaw)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
            setPromptDetails(bankingPrompt)
          } else if (item?.key == 'BankingLoanRaw') {
            setspeechText(bankingLoanRaw)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
            setPromptDetails(bankingPrompt)
          } else if (item?.key == 'InsuranceRaw') {
            setspeechText(insuranceRaw)
            setPromptDetails(insurancePrompt)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
          } else if (item?.key == 'InsurancePharmRaw') {
            setspeechText(insurancePharmRaw)
            setPromptDetails(insurancePrompt)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
          } else if (item?.key == 'InsuranceHealthRaw') {
            setspeechText(insuranceHealthRaw)
            setPromptDetails(insurancePrompt)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
          } else if (item?.key == 'Insurance') {
            setspeechText('')
            setPromptDetails(insurancePrompt)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
          } else {
            setPromptDetails(generalPrompt)
            setSentimentMining('')
            setLanguageExtractiveSummary('')
            setLanguageAbstractiveSummary('')
            setGptPromptSummary('')
            setGptDetails('')
            setGptSummary('')
          }
          setScenario(item)
          setPromptType(promptTypes[promptTypes.findIndex(i => i.key == 'custom')])
    };

    const setLanguages = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        setLanguage(item)
  };

    const generateCustomPrompt = async () => {
        setGptPromptSummary('')
        const requestText = JSON.stringify(speechText)
        const requestCustomPrompt = JSON.stringify(promptDetails)
        //const customParsePrompt = requestText + '\n\n' + requestCustomPrompt
        const customParsePrompt = ''.concat(requestText, '\r\n', requestCustomPrompt)
    
        const request: AskRequest = {
          question: '',
          approach: Approaches.RetrieveThenRead,
          overrides: {
              temperature: temperature,
              chainType: String(selectedChain?.key),
              tokenLength: tokenLength,
          }
        };

        let promptName = 'RealTimeSpeechPrompt'
    
        if (promptType?.key == 'custom') {
          await summarizer(request, customParsePrompt, String(promptType?.key), '', 'inline', 
          String(selectedChain?.key), String(selectedEmbeddingItem?.key)).then((response) => {
            setGptPromptSummary(response)
          }).catch((error) => {
            console.log(error)
            setGptPromptSummary(error)
          })
        } else if (promptType?.key == 'summaryNotes') {
          promptName = 'RtsSummaryNotesPrompt'
        } else if (promptType?.key == 'participants') {
          promptName = 'RtsParticipantsPrompt'
        } else if (promptType?.key == 'followup') {
          promptName = 'RtsFollowupPrompt'
        } else if (promptType?.key == 'pharmacy') {
          promptName = 'RtsPharmacyPrompt'
        } else if (promptType?.key == 'pii') {
          promptName = 'RtsPiiPrompt'
        } else if (promptType?.key == 'topics') {
          promptName = 'RtsTopicsPrompt'
        } else if (promptType?.key == 'complex') {
          promptName = 'RtsComplexPrompt'
        } else {
          promptName = 'RtsGeneralPrompt'
        }
    
        if (promptType?.key != 'custom') {
            const summary = await summarizer(request, requestText, String(promptType?.key), promptName, 'inline', 
            String(selectedChain?.key), String(selectedEmbeddingItem?.key))
            setGptPromptSummary(summary)
        }

        // const url = "https://dataaioaics.openai.azure.com/openai/deployments/davinci/completions?api-version=2022-12-01" 

        // const headers = { 'Content-Type': 'application/json', 'api-key': "8b08d4ba474545c8a93a09847e7298db" }

        // const params = {
        //   prompt: "This is some random text. and some garbage stuff. I am trying to see if this works. tl;dr",
        //   max_tokens: 1000,
        //   temperature: 1,
        // }

        // axios
        //   .post(url, params, { headers: headers })
        //   .then((response: { data: { choices: { text: SetStateAction<string | undefined>; }[]; }; }) => {
        //     setGptPromptSummary(response.data.choices[0].text)
        //   })
        //   .catch((error: string) => {
        //     setGptPromptSummary('FATAL_ERROR amc: ' + error)
        //     console.log(error)
        //   })
    }

    const setPromptTypes = (event?: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
        if (item?.key == 'custom') {
          if (scenario?.key == 'Banking' || scenario?.key == 'BankingRaw' || scenario?.key == 'BankingCcRaw') {
            setPromptDetails(bankingPrompt)
          } else if (
            scenario?.key == 'Insurance' ||
            scenario?.key == 'InsuranceRaw' ||
            scenario?.key == 'InsurancePharmRaw' ||
            scenario?.key == 'InsuranceHealthRaw'
          ) {
            setPromptDetails(insurancePrompt)
          } else if (scenario?.key == 'CapitalMarkets') {
            setPromptDetails(capitalMarketsPrompt)
          } else if (scenario?.key == 'Healthcare') {
            setPromptDetails(healthcarePrompt)
          } else {
            setPromptDetails(generalPrompt)
          }
        } else if (item?.key == 'summaryNotes') {
          setPromptDetails(summaryNotesPrompt)
        } else if (item?.key == 'participants') {
          setPromptDetails(participantPrompt)
        } else if (item?.key == 'followup') {
          setPromptDetails(followupPrompt)
        } else if (item?.key == 'pharmacy') {
          setPromptDetails(pharmacyPrompt)
        } else if (item?.key == 'pii') {
          setPromptDetails(piiPrompt)
        } else if (item?.key == 'topics') {
          setPromptDetails(topicsPrompt)
        } else if (item?.key == 'complex') {
          setPromptDetails(complexPrompt)
        }
        setPromptType(item)
    }

    const getTokenOrRefresh = async () => {
        const tokenResp = await getSpeechToken();
        setSpeechToken(tokenResp.Token)
        setSpeechRegion(tokenResp.Region)
    }

    const speechChange = (ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        setspeechText(newValue || '');
    };

    const promptChange = (ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string): void => {
        setPromptDetails(newValue || '')
    }

    const sttFromMic = async () => {
        setNlpText('')

        if (speechToken === null || speechToken === undefined || speechToken === '') {
            await getTokenOrRefresh()
        }
        const speechConfig = speechsdk.SpeechConfig.fromAuthorizationToken(speechToken, speechRegion)
        speechConfig.speechRecognitionLanguage = language ? String(language?.key) : 'en-US'

        //Setting below specifies custom speech model ID that is created using Speech Studio
        //speechConfig.endpointId = '';

        const audioConfig = speechsdk.AudioConfig.fromDefaultMicrophoneInput()
        recognizer = new speechsdk.SpeechRecognizer(speechConfig, audioConfig)

        let resultText = ''

        recognizer.recognized = async (s: any, e: { result: { reason: ResultReason; text: any; }; }) => {
            if (e.result.reason === ResultReason.RecognizedSpeech) {
                //Display continuous transcript
                resultText += `\n${e.result.text}`
                setspeechText(resultText)

                //Perform continuous NLP
                //const nlpObj = await getKeyPhrases(e.result.text)
                if (e.result.text.length > 1) {
                    const nlpText = await textAnalytics(e.result.text)
                    nlpArray.push(nlpText)
                    setNlpText(nlpArray.join('\r\n'))    
                }
            } else if (e.result.reason === ResultReason.NoMatch) {
                resultText += `\n`
                setspeechText(resultText)
            }
        }
        recognizer.startContinuousRecognitionAsync()
    }

    const sttStop = async () => {
        recognizer.stopContinuousRecognitionAsync()
    }

    const onTemperatureChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
      setTemperature(parseInt(newValue || "0.3"));
    };

    const onTokenLengthChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setTokenLength(parseInt(newValue || "1000"));
    };

    const onChainChange = (event: React.FormEvent<HTMLDivElement>, item?: IDropdownOption): void => {
      setSelectedChain(item);
    };

    useEffect(() => {
        getTokenOrRefresh()
        setChainTypeOptions(chainType)
        setSelectedChain(chainType[0])
        setLanguage(languages[0])
        setSelectedEmbeddingItem(embeddingOptions[0])
    }, [])

    return (
        <div >
            <div >
                <div className={styles.speechTopSection}>
                    <h1 className={styles.speechTitle}>Real-time Speech Analytics</h1>
                </div>
                <div className={styles.speechBottomSection}>
                    <div className={styles.commandsContainer}>
                        <SettingsButton className={styles.settingsButton} onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)} />
                    </div>
                    <br/>
                    <Stack enableScopedSelectors tokens={stackTokens}>
                        <Stack enableScopedSelectors horizontal horizontalAlign="start" styles={stackStyles}>
                            <span style={itemStyles}>
                                    <Label>Languages</Label>&emsp;
                                    <Dropdown
                                        selectedKey={language ? language.key : 'en-us'}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        onChange={setLanguages}
                                        placeholder="Select an Language"
                                        options={languages}
                                        styles={dropdownStyles}
                                    />&emsp; &ensp;
                                    <Label>Scenarios</Label>&emsp;
                                    <Dropdown
                                        selectedKey={scenario ? scenario.key : 'General'}
                                        // eslint-disable-next-line react/jsx-no-bind
                                        onChange={setScenarios}
                                        placeholder="Select an Scenario"
                                        options={scenarioType}
                                        styles={dropdownStyles}
                                    />&emsp; &ensp;
                                    <PrimaryButton onClick={sttFromMic}>
                                       Start Talking
                                    </PrimaryButton> &emsp; &ensp;
                                    <PrimaryButton onClick={sttStop}>
                                        Stop Recording
                                    </PrimaryButton>
                            </span>
                        </Stack>
                        <Stack enableScopedSelectors horizontal horizontalAlign="start" styles={stackStyles}>
                            <span style={itemStyles}>
                                <TextField 
                                    multiline
                                    styles={{root: {width: '700px', height: '500px'}}}
                                    label="Real-time speech transcription"
                                    value={speechText}
                                    rows={25}
                                    onChange={speechChange}
                                />
                            </span>
                            <span style={itemStyles}>
                                &nbsp;&nbsp;&nbsp;&nbsp;
                            </span>
                            <span style={itemStyles}>
                                <TextField 
                                    multiline 
                                    readOnly
                                    styles={{root: {width: '700px', height: '500px'}}}
                                    label="Real-time Insights"
                                    rows={25}
                                    value={nlpText}
                                />
                            </span>
                        </Stack>
                    </Stack>
                    <Stack enableScopedSelectors tokens={stackTokens}>
                        <Stack enableScopedSelectors horizontal horizontalAlign="start" styles={stackStyles}>
                            <span style={itemStyles}>
                                <Label>Prompts</Label>&nbsp;&nbsp;&nbsp;&nbsp;
                                <Dropdown
                                    selectedKey={promptType ? promptType.key : 'custom'}
                                    // eslint-disable-next-line react/jsx-no-bind
                                    onChange={setPromptTypes}
                                    placeholder="Select an Prompt"
                                    options={promptTypes}
                                    styles={dropdownStyles}
                                />&nbsp;&nbsp;&nbsp;&nbsp;
                                <PrimaryButton onClick={generateCustomPrompt}>
                                    OpenAi Summary
                                </PrimaryButton>
                            </span>
                        </Stack>
                        <Stack enableScopedSelectors horizontal horizontalAlign="start" styles={stackStyles}>
                            <span style={itemStyles}>
                                <TextField 
                                    multiline
                                    styles={{root: {width: '400px', height: '500px'}}}
                                    label="Prompt"
                                    value={promptDetails}
                                    rows={12}
                                    onChange={promptChange}
                                />
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
                                    value={gptPromptSummary}
                                    rows={12}
                                />
                            </span>
                        </Stack>
                    </Stack>
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
                        </div>
                        <br/>
                        <SpinButton
                          className={styles.speechSettingsSeparator}
                          label="Set the Temperature:"
                          min={0.0}
                          max={1.0}
                          defaultValue={temperature.toString()}
                          onChange={onTemperatureChange}
                        />
                        <SpinButton
                            className={styles.speechSettingsSeparator}
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
                    </Panel>
                </div>
            </div>
        </div>
    );
};

export default Speech;

