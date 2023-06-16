import { Text } from "@fluentui/react";
import { Settings24Regular } from "@fluentui/react-icons";

import styles from "./QuestionListButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
}

export const QuestionListButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Settings24Regular />
            <Text>{"Question List"}</Text>
        </div>
    );
};
