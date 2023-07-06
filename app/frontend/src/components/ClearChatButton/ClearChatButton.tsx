import { Text } from "@fluentui/react";
import { Delete24Regular } from "@fluentui/react-icons";

import styles from "./ClearChatButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
    disabled?: boolean;
    text: string;
}

export const ClearChatButton = ({ className, disabled, onClick, text }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""} ${disabled && styles.disabled}`} onClick={onClick}>
            <Delete24Regular />
            <Text>{text}</Text>
        </div>
    );
};
