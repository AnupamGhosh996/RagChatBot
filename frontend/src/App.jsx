import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import PDFViewer from './components/PDFViewer';
import FileUpload from './components/FileUpload';
import { api } from './services/api';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [activePdfViewer, setActivePdfViewer] = useState(null); // { document, pageNumber }
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [healthInfo, setHealthInfo] = useState(null);

  // Initialize: load health check & document catalog
  useEffect(() => {
    loadHealthAndDocs();
  }, []);

  const loadHealthAndDocs = async () => {
    try {
      const [health, docs] = await Promise.all([
        api.checkHealth().catch(() => null),
        api.getDocuments().catch(() => [])
      ]);
      setHealthInfo(health);
      setDocuments(docs || []);
    } catch (err) {
      console.error('Initialization error:', err);
    }
  };

  const activeDocument = documents.find(d => d.id === selectedDocId) || null;

  // Send message to RAG backend
  const handleSendMessage = async (questionText) => {
    if (!questionText.trim()) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: questionText,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage({
        question: questionText,
        conversationId: conversationId || undefined,
        documentId: selectedDocId || undefined,
      });

      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        citations: response.citations || [],
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message || 'Error communicating with backend.';
      const errorMessage = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Error:** ${errorDetail}`,
        citations: [],
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      // Refresh health stats to reflect vector count
      api.checkHealth().then(setHealthInfo).catch(() => {});
    }
  };

  // Document upload completion handler
  const handleUploadSuccess = (newDocs) => {
    setDocuments(prev => [...prev, ...newDocs]);
    setIsUploadModalOpen(false);

    if (newDocs && newDocs.length > 0) {
      const firstNewDoc = newDocs[0];
      setSelectedDocId(firstNewDoc.id);

      // Add welcoming suggestion
      const welcomeMsg = {
        id: `sys-${Date.now()}`,
        role: 'assistant',
        content: `✅ Successfully processed and indexed **${firstNewDoc.original_name}** (${firstNewDoc.page_count} pages, ${firstNewDoc.chunk_count} chunks stored in FAISS).\n\nYou can now ask any question about this document, or click one of the suggested prompts below!`,
        citations: [],
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, welcomeMsg]);
    }
  };

  // Delete document
  const handleDeleteDocument = async (docId) => {
    try {
      await api.deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d.id !== docId));
      if (selectedDocId === docId) {
        setSelectedDocId(null);
      }
      if (activePdfViewer && activePdfViewer.document?.id === docId) {
        setActivePdfViewer(null);
      }
      api.checkHealth().then(setHealthInfo).catch(() => {});
    } catch (err) {
      alert(`Failed to delete document: ${err.message}`);
    }
  };

  // Open viewer
  const handleViewDocument = (doc, pageNumber = 1) => {
    setActivePdfViewer({
      document: doc,
      pageNumber: pageNumber || 1,
    });
  };

  // Click on citation in message
  const handleOpenCitation = (citation) => {
    const targetDoc = documents.find(d => d.id === citation.document_id || d.original_name === citation.document_name);
    if (targetDoc) {
      handleViewDocument(targetDoc, citation.page_number || 1);
    } else {
      // Create fallback dummy document object if catalog not yet refreshed
      handleViewDocument({
        id: citation.document_id,
        original_name: citation.document_name,
        page_count: citation.page_number,
      }, citation.page_number || 1);
    }
  };

  // Summarize whole document
  const handleSummarizeDocument = async (doc) => {
    setIsLoading(true);
    const triggerMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: `Summarize the document "${doc.original_name}".`,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, triggerMsg]);

    try {
      const summaryData = await api.generateSummary(doc.id);
      
      let summaryContent = `## Executive Summary for ${doc.original_name}\n\n${summaryData.summary}\n\n`;
      if (summaryData.key_points && summaryData.key_points.length > 0) {
        summaryContent += `### Key Takeaways:\n`;
        summaryData.key_points.forEach(point => {
          summaryContent += `- ${point}\n`;
        });
      }

      const summaryMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: summaryContent,
        citations: [
          {
            document_id: doc.id,
            document_name: doc.original_name,
            page_number: 1,
            chunk_id: `${doc.id}_summary`,
            snippet: `Complete document summary across ${doc.page_count} pages.`
          }
        ],
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, summaryMsg]);
    } catch (err) {
      const errText = err.response?.data?.detail || err.message;
      setMessages(prev => [
        ...prev,
        {
          id: `assistant-err-${Date.now()}`,
          role: 'assistant',
          content: `⚠️ Failed to generate summary: ${errText}`,
          citations: [],
          timestamp: new Date().toISOString(),
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Clear Chat
  const handleClearChat = async () => {
    if (conversationId) {
      await api.clearConversation(conversationId).catch(() => {});
    }
    setMessages([]);
    setConversationId(null);
  };

  // Export Chat to Markdown file
  const handleExportChat = () => {
    if (messages.length === 0) return;

    let md = `# PDF Intelligence - Conversation Export\n`;
    md += `Exported on: ${new Date().toLocaleString()}\n`;
    md += `Total Messages: ${messages.length}\n\n---\n\n`;

    messages.forEach((m) => {
      const roleName = m.role === 'user' ? '👤 User' : '🤖 PDF Intelligence Assistant';
      md += `### ${roleName} (${new Date(m.timestamp).toLocaleTimeString()})\n\n`;
      md += `${m.content}\n\n`;

      if (m.citations && m.citations.length > 0) {
        md += `**Sources & Citations:**\n`;
        m.citations.forEach((c) => {
          md += `- Document: *${c.document_name}*, Page: ${c.page_number}\n`;
          if (c.snippet) {
            md += `  > "${c.snippet}"\n`;
          }
        });
        md += `\n`;
      }
      md += `---\n\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pdf-intelligence-chat-${new Date().toISOString().slice(0, 10)}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0d1117] text-[#e6edf3]">
      {/* Sidebar */}
      <Sidebar
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDocId={(id) => setSelectedDocId(id)}
        onOpenUpload={() => setIsUploadModalOpen(true)}
        onDeleteDocument={handleDeleteDocument}
        onViewDocument={handleViewDocument}
        onSummarizeDocument={handleSummarizeDocument}
        onClearChat={handleClearChat}
        onExportChat={handleExportChat}
        hasChatMessages={messages.length > 0}
        healthInfo={healthInfo}
        isOpen={isSidebarOpen}
        onToggleOpen={setIsSidebarOpen}
      />

      {/* Main Chat Interface */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
        onOpenCitation={handleOpenCitation}
        selectedDoc={activeDocument}
        totalDocuments={documents.length}
        onToggleSidebar={setIsSidebarOpen}
      />

      {/* Embedded PDF Viewer Panel (Side-by-side) */}
      {activePdfViewer && (
        <PDFViewer
          document={activePdfViewer.document}
          initialPage={activePdfViewer.pageNumber}
          onClose={() => setActivePdfViewer(null)}
        />
      )}

      {/* File Upload Modal Overlay */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <FileUpload
            onUploadSuccess={handleUploadSuccess}
            onClose={() => setIsUploadModalOpen(false)}
          />
        </div>
      )}
    </div>
  );
}
