import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Sparkles, 
  Loader2, 
  FileText, 
  Layers, 
  Menu, 
  ArrowDown, 
  HelpCircle,
  FileCheck2
} from 'lucide-react';
import MessageBubble from './MessageBubble';

const SUGGESTED_PROMPTS = [
  "📄 Summarize this document.",
  "💡 What are the most important topics?",
  "🔍 Explain the key concepts in simple terms.",
  "📝 Generate important exam questions based on this text.",
  "🎯 What are the main conclusions and takeaways?"
];

export default function ChatWindow({
  messages = [],
  isLoading = false,
  onSendMessage,
  onOpenCitation,
  selectedDoc = null,
  totalDocuments = 0,
  onToggleSidebar
}) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll on new messages or loading state change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Auto-resize input textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [inputText]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handlePromptClick = (prompt) => {
    if (isLoading) return;
    // Strip emoji if desired, or send directly
    const cleanPrompt = prompt.replace(/^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]\s*/u, '');
    onSendMessage(cleanPrompt);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0d1117] overflow-hidden relative">
      {/* Top Context Bar */}
      <div className="h-14 border-b border-[#1f283a] bg-[#111622]/90 backdrop-blur-md px-4 flex items-center justify-between shrink-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onToggleSidebar(true)}
            className="lg:hidden p-1.5 text-neutral-400 hover:text-white rounded-md bg-[#161f30] border border-[#232f46]"
            title="Toggle Sidebar"
          >
            <Menu className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-2">
            {selectedDoc ? (
              <div className="flex items-center gap-1.5 bg-[#172235] border border-brand-500/30 px-2.5 py-1 rounded-full text-xs text-white">
                <FileText className="w-3.5 h-3.5 text-brand-400" />
                <span className="font-medium max-w-[200px] truncate">{selectedDoc.original_name}</span>
                <span className="text-[10px] text-neutral-400">({selectedDoc.page_count} pages)</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 bg-[#172235] border border-[#2a3850] px-2.5 py-1 rounded-full text-xs text-neutral-300">
                <Layers className="w-3.5 h-3.5 text-brand-400" />
                <span className="font-medium">Searching Across All {totalDocuments} Documents</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-neutral-400">
          <span className="hidden sm:inline-flex items-center gap-1 bg-[#131a26] border border-[#212b3d] px-2 py-0.5 rounded text-[11px]">
            <Sparkles className="w-3 h-3 text-brand-400" />
            Claude RAG Grounded
          </span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="max-w-2xl mx-auto px-4 py-12 flex flex-col items-center justify-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600/20 to-emerald-400/20 border border-brand-500/30 flex items-center justify-center text-brand-400 mb-4 shadow-lg shadow-brand-500/10">
              <Sparkles className="w-7 h-7" />
            </div>

            <h2 className="text-xl font-bold text-white mb-2">
              What would you like to know about your documents?
            </h2>
            <p className="text-xs text-neutral-400 max-w-md mb-8 leading-relaxed">
              Upload PDF documents to extract content, generate vector embeddings, and ask questions with exact page-level citations.
            </p>

            {/* Suggested Question Chips */}
            <div className="w-full text-left">
              <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider block mb-2 px-1">
                Suggested Prompts
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SUGGESTED_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handlePromptClick(prompt)}
                    className="p-3 bg-[#131924] hover:bg-[#182233] border border-[#1f283a] hover:border-brand-500/50 rounded-xl text-left text-xs text-neutral-200 transition-all duration-150 flex items-center justify-between group shadow-sm active:scale-[0.99]"
                  >
                    <span>{prompt}</span>
                    <Sparkles className="w-3.5 h-3.5 text-neutral-500 group-hover:text-brand-400 shrink-0 ml-2 transition-colors" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Message Flow */
          <div className="pb-4">
            {messages.map((msg, i) => (
              <MessageBubble
                key={msg.id || i}
                message={msg}
                onOpenCitation={onOpenCitation}
              />
            ))}

            {/* Generating Thinking Indicator */}
            {isLoading && (
              <div className="py-4 px-4 sm:px-6 bg-[#141b27]/60 border-y border-[#1f283a]">
                <div className="max-w-3xl mx-auto flex gap-3.5 items-center">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="flex items-center gap-2 text-xs text-neutral-400">
                    <span className="font-medium text-neutral-300">Retrieving context & generating answer...</span>
                    <span className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                      <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                      <span className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-bounce"></span>
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Bottom Input Area */}
      <div className="p-4 bg-[#0d1117] border-t border-[#1f283a]">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative bg-[#141b27] border border-[#252f42] focus-within:border-brand-500/60 rounded-xl shadow-lg transition-all">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                selectedDoc
                  ? `Ask a question about "${selectedDoc.original_name}"...`
                  : totalDocuments > 0
                  ? "Ask anything across your uploaded PDF documents..."
                  : "Upload a PDF document first, or ask a question..."
              }
              className="w-full bg-transparent text-sm text-white placeholder-neutral-500 px-4 py-3.5 pr-14 rounded-xl focus:outline-none resize-none max-h-36"
            />

            <div className="absolute right-2.5 bottom-2.5">
              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className="w-8 h-8 rounded-lg bg-brand-600 hover:bg-brand-500 disabled:opacity-30 disabled:hover:bg-brand-600 text-white flex items-center justify-center transition shadow-md shadow-brand-600/30 active:scale-95"
                title="Send question (Enter)"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </form>

          <div className="flex items-center justify-between mt-2 px-1 text-[11px] text-neutral-500">
            <span>Press <kbd className="px-1 py-0.5 bg-[#1b2230] rounded border border-[#2c384e] text-neutral-400">Enter</kbd> to send, <kbd className="px-1 py-0.5 bg-[#1b2230] rounded border border-[#2c384e] text-neutral-400">Shift + Enter</kbd> for newline</span>
            <span>All answers strictly cited from PDF text</span>
          </div>
        </div>
      </div>
    </div>
  );
}
