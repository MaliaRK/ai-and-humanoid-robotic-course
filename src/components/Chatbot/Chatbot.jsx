import React, { useState, useRef, useEffect } from 'react';
import { generateUUID } from './utils';
import './Chatbot.module.css';
import ChatInput from './ChatInput';
import MessageList from './MessageList';

/**
 * Main Chatbot component that integrates with the RAG backend
 */
const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  /**
   * Handles submitting a query to the RAG backend
   * @param {string} query - The user's query
   * @param {string} selectedText - Optional selected text for context
   */
  const handleSubmit = async (query, selectedText = null) => {
    if (!query.trim()) return;

    // Add user message to the chat
    const userMessage = {
      id: generateUUID(),
      text: query,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Prepare the request payload - match the backend API schema
      const requestBody = {
        query: query,
        ...(selectedText && { selected_text: selectedText }),
        ...(conversationId && { conversation_id: conversationId }),
      };

      // Call the RAG backend API - use full URL to backend server
      const BACKEND_URL = 'https://ai-book-production.up.railway.app/';
      const response = await fetch(`${BACKEND_URL}/api/v1/rag/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Backend API error: ${response.status}`);
      }

      const data = await response.json();

      // Update conversation ID if new one was generated
      if (data.conversationId && !conversationId) {
        setConversationId(data.conversationId);
      }

      // Create the AI response message
      const aiMessage = {
        id: data.id,
        text: data.response,
        sender: 'ai',
        timestamp: new Date().toISOString(),
        citations: data.citations || [],
        confidence: data.confidence,
      };

      // Add the AI response to the chat
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error calling RAG backend:', error);

      // Add an error message to the chat
      const errorMessage = {
        id: generateUUID(),
        text: `Sorry, I encountered an error processing your request: ${error.message}`,
        sender: 'system',
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <h3>AI Assistant</h3>
      </div>
      <MessageList messages={messages} />
      <div ref={messagesEndRef} />
      <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  );
};

export default Chatbot;