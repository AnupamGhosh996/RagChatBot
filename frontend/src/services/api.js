import axios from 'axios';

const API_BASE = '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s timeout for large PDF embedding generation
});

export const api = {
  // Check backend health & status
  checkHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Get list of uploaded documents
  getDocuments: async () => {
    const res = await apiClient.get('/documents');
    return res.data;
  },

  // Upload one or more PDFs with progress tracking
  uploadPDFs: async (fileList, onProgress) => {
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
      formData.append('files', fileList[i]);
    }

    const res = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentCompleted);
        }
      },
    });
    return res.data;
  },

  // Delete a document and its indexed vectors
  deleteDocument: async (documentId) => {
    const res = await apiClient.delete(`/documents/${documentId}`);
    return res.data;
  },

  // Ask question with RAG context
  sendChatMessage: async ({ question, conversationId, documentId }) => {
    const res = await apiClient.post('/chat', {
      question,
      conversation_id: conversationId || undefined,
      document_id: documentId || undefined,
    });
    return res.data;
  },

  // Request comprehensive document summary
  generateSummary: async (documentId) => {
    const res = await apiClient.post('/summary', {
      document_id: documentId,
    });
    return res.data;
  },

  // Get conversation history
  getConversationHistory: async (conversationId) => {
    const res = await apiClient.get(`/history/${conversationId}`);
    return res.data;
  },

  // Clear conversation history
  clearConversation: async (conversationId) => {
    const res = await apiClient.delete(`/history/${conversationId}`);
    return res.data;
  },

  // Helper to get PDF view URL with page anchor
  getPDFViewerUrl: (documentId, pageNumber = 1) => {
    return `/api/documents/${documentId}/file#page=${pageNumber}&view=FitH`;
  },
};
