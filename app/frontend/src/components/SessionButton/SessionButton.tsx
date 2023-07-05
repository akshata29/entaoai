import { Text } from "@fluentui/react";
import { Add24Regular } from "@fluentui/react-icons";

import styles from "./SessionButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
}

export const SessionButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Add24Regular />
            <Text>{"New Session"}</Text>
        </div>
    );
};
