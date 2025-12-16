import React from 'react';
import DefaultDocRoot from '@theme-original/DocRoot';
import Chatbot from '@site/src/components/Chatbot/Chatbot';
import styles from './styles.module.css';

export default function DocRoot(props) {
  return (
    <>
      <DefaultDocRoot {...props} />
      <div className={styles.chatbotContainer}>
        <div className={styles.chatbotWrapper}>
          <Chatbot />
        </div>
      </div>
    </>
  );
}