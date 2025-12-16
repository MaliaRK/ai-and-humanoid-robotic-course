/**
 * Utility functions for the Chatbot component
 */

/**
 * Generate a UUID for message and conversation identification
 * @returns {string} A UUID string
 */
export const generateUUID = () => {
  // Use crypto.randomUUID if available (modern browsers)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback for older browsers
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

/**
 * Extract selected text from the page using the Selection API
 * @returns {string|null} The selected text or null if no text is selected
 */
export const getSelectedText = () => {
  if (typeof window === 'undefined' || !window.getSelection) {
    return null;
  }

  const selection = window.getSelection();
  const selectedText = selection.toString().trim();

  return selectedText.length > 0 ? selectedText : null;
};

/**
 * Get the coordinates of the current selection
 * @returns {Object|null} Object with x, y coordinates or null if no selection
 */
export const getSelectionCoordinates = () => {
  const selection = window.getSelection();

  if (selection.rangeCount === 0) {
    return null;
  }

  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  return {
    x: rect.left + window.scrollX,
    y: rect.top + window.scrollY,
    width: rect.width,
    height: rect.height
  };
};

/**
 * Format a timestamp for display
 * @param {string|Date} timestamp - The timestamp to format
 * @returns {string} Formatted time string
 */
export const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

/**
 * Validate query parameters
 * @param {string} query - The query string to validate
 * @returns {Array} Array of validation errors
 */
export const validateQuery = (query) => {
  const errors = [];

  if (!query || typeof query !== 'string') {
    errors.push('Query is required and must be a string');
  } else if (query.trim().length === 0) {
    errors.push('Query cannot be empty or whitespace only');
  } else if (query.trim().length < 3) {
    errors.push('Query must be at least 3 characters long');
  } else if (query.trim().length > 1000) {
    errors.push('Query exceeds maximum length of 1000 characters');
  }

  return errors;
};

/**
 * Validate selected text
 * @param {string|null} selectedText - The selected text to validate
 * @returns {Array} Array of validation errors
 */
export const validateSelectedText = (selectedText) => {
  const errors = [];

  if (selectedText) {
    if (typeof selectedText !== 'string') {
      errors.push('Selected text must be a string');
    } else if (selectedText.length < 10) {
      errors.push('Selected text must be at least 10 characters long');
    } else if (selectedText.length > 5000) {
      errors.push('Selected text exceeds maximum length of 5000 characters');
    }
  }

  return errors;
};

/**
 * Validate conversation ID
 * @param {string|null} conversationId - The conversation ID to validate
 * @returns {Array} Array of validation errors
 */
export const validateConversationId = (conversationId) => {
  const errors = [];

  if (conversationId) {
    if (typeof conversationId !== 'string') {
      errors.push('Conversation ID must be a string');
    } else if (conversationId.length > 100) {
      errors.push('Conversation ID exceeds maximum length of 100 characters');
    }
  }

  return errors;
};

/**
 * Validate scope parameter
 * @param {string|null} scope - The scope to validate
 * @returns {Array} Array of validation errors
 */
export const validateScope = (scope) => {
  const validScopes = ['course', 'modules', 'readings', 'assignments', 'general'];
  const errors = [];

  if (scope && typeof scope === 'string') {
    if (!validScopes.includes(scope.toLowerCase())) {
      errors.push(`Invalid scope: ${scope}. Valid scopes are: ${validScopes.join(', ')}`);
    }
  } else if (scope && typeof scope !== 'string') {
    errors.push('Scope must be a string');
  }

  return errors;
};

/**
 * Sanitize text to prevent XSS
 * @param {string} text - The text to sanitize
 * @returns {string} Sanitized text
 */
export const sanitizeText = (text) => {
  if (typeof text !== 'string') {
    return '';
  }

  // Basic sanitization to prevent XSS
  return text
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
};

/**
 * Format response text for display
 * @param {string} text - The response text to format
 * @returns {string} Formatted text
 */
export const formatResponseText = (text) => {
  if (typeof text !== 'string') {
    return '';
  }

  // Basic formatting to improve readability
  return text.replace(/\n+/g, '<br />');
};

/**
 * Check if the current environment is suitable for the chatbot
 * @returns {boolean} Whether the environment is supported
 */
export const isEnvironmentSupported = () => {
  // Check for required APIs
  return typeof window !== 'undefined' &&
         typeof window.getSelection === 'function' &&
         typeof fetch === 'function' &&
         typeof Promise !== 'undefined';
};

/**
 * Debounce a function call
 * @param {Function} func - The function to debounce
 * @param {number} wait - The wait time in milliseconds
 * @param {boolean} immediate - Whether to execute immediately
 * @returns {Function} The debounced function
 */
export const debounce = (func, wait, immediate = false) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      timeout = null;
      if (!immediate) func.apply(this, args);
    };
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(this, args);
  };
};