import {
    DocumentCard,
    DocumentCardDetails,
    DocumentCardPreview,
    DocumentCardTitle,
    DocumentCardType,
  } from '@fluentui/react/lib/DocumentCard';
import { Stack, IStackTokens } from '@fluentui/react/lib/Stack';

import styles from "./MediaCard.module.css";
const stackTokens: IStackTokens = { childrenGap: 20 };

interface Props {
    cardData: any;
}

export const MediaCard = ({ cardData }: Props) => {
    return cardData !== null ? (
        <div>
            <Stack enableScopedSelectors tokens={stackTokens} className={styles.container}>
                <Stack.Item grow={2}>
                    {cardData.map((item: any) => (
                        <DocumentCard aria-label= "" type={DocumentCardType.compact} onClickHref={item.url}>
                            <DocumentCardTitle title={item.title} shouldTruncate className={styles.questionInputContainer}/>
                            <DocumentCardTitle title={item.text} className={styles.questionInputContainer} />
                        </DocumentCard>
                    ))}
                </Stack.Item>
            </Stack>
        </div>
    ) : (
        <div>No data</div>
    );
};
