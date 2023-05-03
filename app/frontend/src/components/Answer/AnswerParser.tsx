import { renderToStaticMarkup } from "react-dom/server";
import { getCitationFilePath } from "../../api";
import { Link } from "react-router-dom";
import { logger } from "@azure/storage-blob";

type HtmlParsedAnswer = {
    answerHtml: string;
    citations: string[];
    followupQuestions: string[];
};

export function parseAnswerToHtml(answer: string, 
    onCitationClicked: (citationFilePath: string) => void, sources: string, nextQuestions: string): HtmlParsedAnswer {
    let citations: string[] = [];
    const dupCitations: string[] = [];
    const followupQuestions: string[] = [];

    // Extract any follow-up questions that might be in the answer
    nextQuestions.replace(/<([^>]+)>/g, (match, content) => {
        followupQuestions.push(content);
        return "";
    });

    if (followupQuestions.length == 0) {
        nextQuestions.split('\n').map((part, index) => {
            if (part.trim().length > 0) {
                followupQuestions.push(part);
            }
        });
    }
    // var expression = /(https?:\/\/[^ ]*)/;
    var expression = /(?:[^/][\d\w\.]+)$(?<=\.\w{3,4})/;

    // nextQuestions.split('\n').map((part, index) => {
    //     if (part.trim().length > 0) {
    //         followupQuestions.push(part);
    //     }
    // });

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
                citationIndex = citations.length;
            }

            const path = getCitationFilePath(part);
            // const name = part.split(',')[0].replace('-', '');
            // let url = part.split(',')[1];
            // if (url == undefined) {
            //     if (part.match(expression)) {
            //         url = part.match(expression)[1];
            //     }
            // }
            if (part.indexOf('blob.core.windows.net') > -1) { 
                const fileName  = part.substring(part.lastIndexOf('/')+1).replaceAll('%20', ' ');
                if (fileName.trim() != "") {
                    dupCitations.push(fileName);
                } else if (part.match(expression))
                {
                    const fileName = part.match(expression)![0];
                    if (fileName.trim() != "") {
                        dupCitations.push(fileName);
                    }
                }
            } 
            else {
                if (part.indexOf('http') > -1 || part.indexOf('.pdf') > -1 || part.indexOf('https') > -1) {
                    dupCitations.push(part);
                }
            }       
        }
        citations = [...new Set(dupCitations)];

    });

    return {
        answerHtml: answer,
        citations,
        followupQuestions
    };
}
