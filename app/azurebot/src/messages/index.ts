import { AzureFunction, Context, HttpRequest } from "@azure/functions"
import { Response } from "botbuilder";
import { ChatGpt } from "../modules/ChatGpt";
import { BotAdapterInstance } from "../modules/BotAdapter";
import { MemoryStorage, UserState, TurnContext } from 'botbuilder';

let userState: UserState;
const indexProperty = 'IndexProperty';

const httpTrigger: AzureFunction = async function (context: Context, req: HttpRequest): Promise<void> {

    req.params.indexType = "pinecone";
    req.params.indexNs = "d06ced81b60b4d34a30f073bbf4ed5d1";
    // userState = new UserState(new MemoryStorage());
    // const indexInformation = userState.createProperty(indexProperty);
    // const turnContext: TurnContext = TurnContext.apply(context);
    // const index = await indexInformation.get(turnContext, {});

    // index.indexType = req.params.indexType;
    // index.indexNs = req.params.indexNs;
    
    // Create bot
    const bot = new ChatGpt(req.params.indexType, req.params.indexNs);

    // Process request
    const botAdapterInstance = BotAdapterInstance.getInstance();
    await botAdapterInstance.adapter.process(req, context.res as Response, (context) => bot.run(context));

};

export default httpTrigger;