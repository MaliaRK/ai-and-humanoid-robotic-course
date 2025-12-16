import React from 'react';

/**
 * MessageList component to display chat messages
 */
const MessageList = ({ messages }) => {
  /**
   * Format timestamp for display
   */
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  /**
   * Render citations for AI responses
   */
  const renderCitations = (citations) => {
    if (!citations || citations.length === 0) {
      return null;
    }

    return (
      <div className="citations">
        <strong>Citations:</strong>
        {citations.map((citation, index) => (
          <div key={index} className="citation-item">
            <a
              href={citation.url}
              className="citation-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              {citation.module} (Chunk {citation.chunkId})
            </a>
            {citation.textPreview && (
              <div className="citation-preview">
                "{citation.textPreview.substring(0, 100)}{citation.textPreview.length > 100 ? '...' : ''}"
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="message-list">
      {messages.length === 0 ? (
        <div className="welcome-message">
          <p>Hello! I'm your AI assistant for the AI & Humanoid Robotics course.</p>
          <p>Ask me any questions about the documentation, or select text and ask about it specifically.</p>
        </div>
      ) : (
        messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.sender}-message`}
          >
            <div className="message-text">{message.text}</div>
            {message.timestamp && (
              <div className="message-timestamp">
                {formatTimestamp(message.timestamp)}
              </div>
            )}
            {message.sender === 'ai' && message.citations && (
              <>
                {renderCitations(message.citations)}
                {typeof message.confidence !== 'undefined' && (
                  <div className="confidence-score">
                    Confidence: {(message.confidence * 100).toFixed(1)}%
                  </div>
                )}
              </>
            )}
          </div>
        ))
      )}
    </div>
  );
};

export default MessageList;