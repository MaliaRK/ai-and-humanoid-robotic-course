/**
 * API Client for communicating with the RAG backend
 */

class RAGApiClient {
  constructor(baseURL = 'http://localhost:8085') {
    this.baseURL = baseURL;
  }

  /**
   * Submit a query to the RAG backend
   * @param {Object} params - Query parameters
   * @param {string} params.query - The user's query
   * @param {string} [params.selectedText] - Optional selected text for context
   * @param {string} [params.scope] - Query scope (course, modules, etc.)
   * @param {string} [params.conversationId] - Existing conversation ID
   * @returns {Promise<Object>} Response from the backend
   */
  async query(params) {
    const {
      query,
      selectedText = null,
      scope = 'general',
      conversationId = null
    } = params;

    // Validate required parameters
    if (!query || typeof query !== 'string' || query.trim().length === 0) {
      throw new Error('Query is required and must be a non-empty string');
    }

    // Prepare the request payload
    const requestBody = {
      query: query.trim(),
      scope: scope,
      ...(selectedText && { selectedText: selectedText.trim() }),
      ...(conversationId && { conversationId })
    };

    try {
      const response = await fetch(`${this.baseURL}/api/v1/rag/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        // Handle different error statuses
        switch (response.status) {
          case 400:
            throw new Error(`Bad Request: ${errorData.message || 'Invalid parameters'}`);
          case 429:
            throw new Error('Rate limit exceeded. Please try again later.');
          case 500:
            throw new Error(`Internal Server Error: ${errorData.message || 'Backend service error'}`);
          default:
            throw new Error(`API Error (${response.status}): ${errorData.message || 'Unknown error'}`);
        }
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error: Unable to reach the backend service. Please check if the server is running.');
      }
      throw error;
    }
  }

  /**
   * Verify that the backend API is accessible
   * @returns {Promise<boolean>} Whether the API is reachable
   */
  async verifyConnection() {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch (error) {
      console.warn('API connection verification failed:', error);
      return false;
    }
  }

  /**
   * Get health status of the RAG system
   * @returns {Promise<Object>} Health status information
   */
  async getHealthStatus() {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/rag/health`);

      if (!response.ok) {
        throw new Error(`Health check failed with status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting health status:', error);
      throw error;
    }
  }

  /**
   * Get conversation history
   * @param {string} conversationId - The conversation ID to retrieve
   * @returns {Promise<Object>} Conversation data
   */
  async getConversation(conversationId) {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/rag/conversations/${conversationId}`);

      if (!response.ok) {
        throw new Error(`Failed to get conversation with status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error getting conversation:', error);
      throw error;
    }
  }
}

// Export singleton instance
const apiClient = new RAGApiClient();
export default apiClient;

// Also export the class for testing or alternative instantiation
export { RAGApiClient };