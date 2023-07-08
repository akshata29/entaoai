import { Text } from "@fluentui/react";
import { Rename24Regular } from "@fluentui/react-icons";

import styles from "./RenameButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
    text: string;
}

export const RenameButton = ({ className, onClick, text }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Rename24Regular />
            <Text>{text}</Text>
        </div>
    );
};
