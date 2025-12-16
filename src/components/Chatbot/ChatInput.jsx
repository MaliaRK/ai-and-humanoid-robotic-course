import React, { useState, useRef } from 'react';
import { getSelectedText as getSelectedTextUtil, validateQuery as validateQueryUtil, validateSelectedText as validateSelectedTextUtil } from './utils';

/**
 * ChatInput component for user queries with text selection support
 */
const ChatInput = ({ onSubmit, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState(null);
  const textareaRef = useRef(null);

  /**
   * Handle form submission
   */
  const handleSubmit = (e) => {
    e.preventDefault();

    if (!inputValue.trim() || isLoading) return;

    // Validate the query
    const queryErrors = validateQueryUtil(inputValue);
    if (queryErrors.length > 0) {
      setError(queryErrors[0]); // Show the first validation error
      return;
    }

    // Get any selected text on the page
    const selectedTextOnPage = getSelectedTextUtil();

    // Validate selected text if present
    if (selectedTextOnPage) {
      const selectedTextErrors = validateSelectedTextUtil(selectedTextOnPage);
      if (selectedTextErrors.length > 0) {
        setError(selectedTextErrors[0]); // Show the first validation error
        return;
      }
    }

    // Clear any previous errors
    setError(null);

    // Submit the query with selected text context
    onSubmit(inputValue, selectedTextOnPage);

    // Clear the input
    setInputValue('');
  };

  /**
   * Handle input changes
   */
  const handleInputChange = (e) => {
    const newValue = e.target.value;
    setInputValue(newValue);

    // Clear error when user starts typing
    if (error) {
      const queryErrors = validateQueryUtil(newValue);
      if (queryErrors.length === 0) {
        setError(null);
      }
    }
  };

  /**
   * Handle pressing Enter key (without Shift)
   */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Get any currently selected text to show as a contextual indicator
  const currentSelectedText = getSelectedTextUtil();

  return (
    <div className="chat-input-container">
      {currentSelectedText && (
        <div className="selected-text-indicator">
          Selected text: "{currentSelectedText.substring(0, 50)}{currentSelectedText.length > 50 ? '...' : ''}"
        </div>
      )}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      <form className="input-form" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the documentation..."
          rows="2"
          disabled={isLoading}
          aria-label="Chat input"
        />
        <button
          type="submit"
          className="submit-button"
          disabled={!inputValue.trim() || isLoading}
          aria-label="Submit query"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;