import React, { createContext, useContext, useReducer } from 'react';

// Create the chat context
const ChatContext = createContext();

// Initial state for the chat
const initialState = {
  messages: [],
  isLoading: false,
  conversationId: null,
  error: null,
  selectedText: null,
};

// Reducer to handle chat state updates
const chatReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.isLoading,
      };
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.message],
      };
    case 'SET_CONVERSATION_ID':
      return {
        ...state,
        conversationId: action.conversationId,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'SET_SELECTED_TEXT':
      return {
        ...state,
        selectedText: action.selectedText,
      };
    case 'RESET_CHAT':
      return {
        ...initialState,
      };
    default:
      return state;
  }
};

// Provider component to wrap the chat components
export const ChatProvider = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  // Actions to update the state
  const setLoading = (isLoading) => {
    dispatch({ type: 'SET_LOADING', isLoading });
  };

  const addMessage = (message) => {
    dispatch({ type: 'ADD_MESSAGE', message });
  };

  const setConversationId = (conversationId) => {
    dispatch({ type: 'SET_CONVERSATION_ID', conversationId });
  };

  const setError = (error) => {
    dispatch({ type: 'SET_ERROR', error });
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const setSelectedText = (selectedText) => {
    dispatch({ type: 'SET_SELECTED_TEXT', selectedText });
  };

  const resetChat = () => {
    dispatch({ type: 'RESET_CHAT' });
  };

  const value = {
    ...state,
    setLoading,
    addMessage,
    setConversationId,
    setError,
    clearError,
    setSelectedText,
    resetChat,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

// Custom hook to use the chat context
export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};