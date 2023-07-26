import { useMemo } from "react";
import { Stack } from "@fluentui/react";
import DOMPurify from "dompurify";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";

import styles from "./Answer.module.css";

import { AskResponse } from "../../api";
import { AnswerIcon } from "./AnswerIcon";

interface Props {
    answer: string;
}

export const AnswerChat = ({
    answer
}: Props) => {
    
    const sanitizedAnswerHtml = DOMPurify.sanitize(answer);
    return (
        <Stack className={`${styles.answerContainer}`} verticalAlign="space-between">
            <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                </Stack>
            </Stack.Item>

            <Stack.Item grow>
                <div className={styles.answerText}>
                    <ReactMarkdown children={sanitizedAnswerHtml} rehypePlugins={[rehypeRaw]} />
                </div>
            </Stack.Item>
        </Stack>
    );
};
