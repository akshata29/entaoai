import { ActivityHandler, CardFactory, MessageFactory, BotState, MemoryStorage, TurnContext } from "botbuilder";
import * as ACData from "adaptivecards-templating";
import * as AnswerCard from "../cards/Answer.json";
import { ChatResponse, ChatTurn, AskResponse } from "../api";

let answers: [string, AskResponse][] = [];
const indexProperty = 'IndexProperty';

export class ChatGpt extends ActivityHandler {
    private userState: BotState;
    //constructor(userState: BotState) {
    constructor(indexType: string, indexNs: string) {
        super();

        //const indexInformation = userState.createProperty(indexProperty);

        this.onMessage(async (context, next) => {

            //const index = await indexInformation.get(context, {});

            try {
                try{
                    const history: ChatTurn[] = answers.map(a => ({ user: a[0], bot: a[1].answer }));
                    const url = process.env.ChatGptUrl + "&indexType=" + indexType + "&indexNs=" + indexNs
                    const reqBody = {
                        values: [
                        {
                            recordId: 0,
                            data: {
                            history: [...history, { user: context.activity.text, bot: undefined }],
                            approach: 'rrr',
                            overrides: {
                                semantic_ranker: true,
                                semantic_captions: false,
                                top: 3,
                                suggest_followup_questions: false
                            }
                            }
                        }
                        ]
                    }
                    console.log(reqBody)
                    const response = await fetch(url, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify(reqBody)
                    });
                    const parsedResponse: ChatResponse = await response.json();
                    const result = parsedResponse.values[0].data

                    answers = [...answers, [context.activity.text, result]]
                    const replyText = result.answer;

                    // Create data for card
                    const cardData = {
                        answer: replyText
                    }

                    const template = new ACData.Template(AnswerCard);
                    const cardPayload = template.expand({ $root: cardData });
                    const card = CardFactory.adaptiveCard(cardPayload);
                    //await context.sendActivity(MessageFactory.attachment(card));
                    await context.sendActivity(replyText)

                }
                catch(e){
                    console.log(e)
                }

            } catch (e) {
                console.log(e);
            } finally {
            }

            await next();
        });

        this.onMembersAdded(async (context, next) => {
            const membersAdded = context.activity.membersAdded;
            const welcomeText = 'Hi, this is ChatGPT model! How can I help you?';
            answers = []
            for (const member of membersAdded) {
                if (member.id !== context.activity.recipient.id) {
                    await context.sendActivity(MessageFactory.text(welcomeText, welcomeText));
                }
            }
            // By calling next() you ensure that the next BotHandler is run.
            await next();
        });
    }

    async run(context) {
        await super.run(context);
        // Save any state changes. The load happened during the execution of the Dialog.
        await this.userState.saveChanges(context, false);
    }
}