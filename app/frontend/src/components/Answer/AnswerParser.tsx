import { renderToStaticMarkup } from "react-dom/server";
import { getCitationFilePath } from "../../api";

type HtmlParsedAnswer = {
    answerHtml: string;
    citations: string[];
    followupQuestions: string[];
};

export function parseAnswerToHtml(answer: string, 
    onCitationClicked: (citationFilePath: string) => void, sources: string, nextQuestions: string): HtmlParsedAnswer {
    const citations: string[] = [];
    const followupQuestions: string[] = [];

    // Extract any follow-up questions that might be in the answer
    // nextQuestions.replace(/<([^>]+)>/g, (match, content) => {
    //     followupQuestions.push(content);
    //     return "";
    // });
    nextQuestions.split('\n').map((part, index) => {
        if (part.trim().length > 0) {
            followupQuestions.push(part);
        }
    });

    // trim any whitespace from the end of the answer after removing follow-up questions
    //let parsedThoughts = sources.trim().replace("NEXT QUESTIONS:", "").replace("GENERATED FOLLOW-UP QUESTIONS:", "");

    // const parts = parsedThoughts.split(/\[([^\]]+)\]/g);
    // const fragments: string[] = parts.map((part, index) => {
    //     if (index % 2 === 0) {
    //         return part;
    //     } else {
    //         let citationIndex: number;
    //         if (citations.indexOf(part) !== -1) {
    //             citationIndex = citations.indexOf(part) + 1;
    //         } else {
    //             citations.push(part);
    //             citationIndex = citations.length;
    //         }
    //         const path = getCitationFilePath(part);

    //         return renderToStaticMarkup(
    //             <a className="supContainer" title={part} onClick={() => onCitationClicked(path)}>
    //                 <sup>{citationIndex}</sup>
    //             </a>
    //         );
    //     }
    // });

    let parts = sources.split(',');
    parts = sources.split('\n');
    parts.map((part, index) => {
        if (part.trim().length > 0) {
            let citationIndex: number;
            if (citations.indexOf(part) !== -1) {
                citationIndex = citations.indexOf(part) + 1;
            } else {
                citations.push(part);
                citationIndex = citations.length;
            }
            const path = getCitationFilePath(part);

            return renderToStaticMarkup(
                <a className="supContainer" title={part} onClick={() => onCitationClicked(path)}>
                    <sup>{citationIndex}</sup>
                </a>
            );
        }
    });

    return {
        answerHtml: answer,
        citations,
        followupQuestions
    };
}
