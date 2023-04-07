import { CloudAdapter, 
    ConfigurationServiceClientCredentialFactory, 
    createBotFrameworkAuthenticationFromConfiguration } from "botbuilder";

export class BotAdapterInstance {
    private static instance: BotAdapterInstance;
    adapter: CloudAdapter;

    private constructor() {
        try {
            // Build bot credentials
            const credentialsFactory = new ConfigurationServiceClientCredentialFactory({
                MicrosoftAppId: process.env.MicrosoftAppId,
                MicrosoftAppPassword: process.env.MicrosoftAppPassword,
                MicrosoftAppType: process.env.MicrosoftAppType,
                MicrosoftAppTenantId: process.env.MicrosoftAppTenantId
            });
            // Create bot authentication
            const botFrameworkAuthentication = createBotFrameworkAuthenticationFromConfiguration(null, credentialsFactory);
            // Create bot adapter
            this.adapter = new CloudAdapter(botFrameworkAuthentication);

        } catch (err) {
            const error = err as any;
            throw new Error(error);
        }
    }

    public static getInstance(): BotAdapterInstance {
        if (!this.instance) {
            this.instance = new this();
        }

        return this.instance;
    }

}