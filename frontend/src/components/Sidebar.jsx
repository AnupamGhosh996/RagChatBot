import React, { useState } from 'react';
import { 
  FileText, 
  Trash2, 
  Plus, 
  Layers, 
  Sparkles, 
  Eye, 
  Download, 
  RotateCcw, 
  Database,
  CheckCircle,
  Menu,
  X,
  FileSpreadsheet
} from 'lucide-react';

export default function Sidebar({
  documents = [],
  selectedDocId = null,
  onSelectDocId,
  onOpenUpload,
  onDeleteDocument,
  onViewDocument,
  onSummarizeDocument,
  onClearChat,
  onExportChat,
  hasChatMessages,
  healthInfo,
  isOpen,
  onToggleOpen
}) {
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm"
          onClick={() => onToggleOpen(false)}
        />
      )}

      {/* Main Sidebar Container */}
      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-72 bg-[#101623] border-r border-[#1f283a] flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top Header */}
        <div className="p-4 border-b border-[#1f283a] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-tight">PDF Intelligence</h1>
              <p className="text-[11px] text-neutral-400">RAG Document Assistant</p>
            </div>
          </div>
          <button
            onClick={() => onToggleOpen(false)}
            className="lg:hidden p-1 text-neutral-400 hover:text-white rounded"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Upload Action Button */}
        <div className="p-3">
          <button
            onClick={onOpenUpload}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-brand-600 to-emerald-600 hover:from-brand-500 hover:to-emerald-500 text-white font-medium py-2 px-3 rounded-lg text-xs shadow-md shadow-brand-600/20 transition-all duration-150 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>Upload New PDF</span>
          </button>
        </div>

        {/* Cross-document Scope Selector */}
        <div className="px-3 pb-2">
          <button
            onClick={() => onSelectDocId(null)}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-colors ${
              selectedDocId === null
                ? 'bg-brand-500/15 border border-brand-500/40 text-brand-300 font-semibold'
                : 'text-neutral-400 hover:bg-[#161f30] hover:text-neutral-200'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              <Layers className="w-3.5 h-3.5 text-brand-400 shrink-0" />
              <span className="truncate">Search All Documents</span>
            </div>
            <span className="text-[10px] bg-[#1a2335] px-1.5 py-0.5 rounded text-neutral-400 border border-[#27354f]">
              {documents.length}
            </span>
          </button>
        </div>

        {/* Uploaded Documents List */}
        <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
          <div className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider px-2 py-1">
            Uploaded PDFs ({documents.length})
          </div>

          {documents.length === 0 ? (
            <div className="p-4 text-center text-xs text-neutral-500 border border-dashed border-[#222d3f] rounded-lg">
              No PDFs uploaded yet. Click above to add documents.
            </div>
          ) : (
            documents.map((doc) => {
              const isSelected = selectedDocId === doc.id;
              return (
                <div
                  key={doc.id}
                  onClick={() => onSelectDocId(doc.id)}
                  className={`group relative p-2.5 rounded-lg border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#182335] border-brand-500/50 text-white shadow-sm'
                      : 'bg-[#121824] hover:bg-[#162030] border-[#1d2738] text-neutral-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <FileText className={`w-4 h-4 shrink-0 ${isSelected ? 'text-brand-400' : 'text-neutral-400'}`} />
                      <span className="text-xs font-medium truncate" title={doc.original_name}>
                        {doc.original_name}
                      </span>
                    </div>

                    {/* Quick action buttons */}
                    <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity">
                      {/* View PDF */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewDocument(doc, 1);
                        }}
                        className="p-1 text-neutral-400 hover:text-white hover:bg-[#222e44] rounded"
                        title="View PDF"
                      >
                        <Eye className="w-3 h-3" />
                      </button>

                      {/* Summarize */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSummarizeDocument(doc);
                        }}
                        className="p-1 text-neutral-400 hover:text-brand-400 hover:bg-[#222e44] rounded"
                        title="Generate AI Summary"
                      >
                        <Sparkles className="w-3 h-3" />
                      </button>

                      {/* Delete */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirmDeleteId === doc.id) {
                            onDeleteDocument(doc.id);
                            setConfirmDeleteId(null);
                          } else {
                            setConfirmDeleteId(doc.id);
                            setTimeout(() => setConfirmDeleteId(null), 3000);
                          }
                        }}
                        className={`p-1 rounded transition ${
                          confirmDeleteId === doc.id
                            ? 'bg-red-600 text-white animate-pulse'
                            : 'text-neutral-400 hover:text-red-400 hover:bg-[#222e44]'
                        }`}
                        title={confirmDeleteId === doc.id ? "Click again to confirm delete" : "Delete document"}
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Metadata line */}
                  <div className="flex items-center gap-2 mt-1.5 text-[10px] text-neutral-400">
                    <span>{doc.file_size_formatted}</span>
                    <span>•</span>
                    <span>{doc.page_count} {doc.page_count === 1 ? 'page' : 'pages'}</span>
                    <span>•</span>
                    <span className="text-neutral-500">{doc.chunk_count} chunks</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer controls: Clear chat, Export, Health indicator */}
        <div className="p-3 border-t border-[#1f283a] space-y-2 bg-[#0d121c]">
          <div className="flex items-center gap-2">
            <button
              onClick={onClearChat}
              disabled={!hasChatMessages}
              className="flex-1 flex items-center justify-center gap-1.5 bg-[#161e2c] hover:bg-[#1e293c] disabled:opacity-40 disabled:hover:bg-[#161e2c] text-neutral-300 text-xs py-1.5 px-2 rounded-md border border-[#273347] transition"
              title="Clear conversation"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear Chat</span>
            </button>

            <button
              onClick={onExportChat}
              disabled={!hasChatMessages}
              className="flex-1 flex items-center justify-center gap-1.5 bg-[#161e2c] hover:bg-[#1e293c] disabled:opacity-40 disabled:hover:bg-[#161e2c] text-neutral-300 text-xs py-1.5 px-2 rounded-md border border-[#273347] transition"
              title="Export chat history as Markdown"
            >
              <Download className="w-3 h-3" />
              <span>Export</span>
            </button>
          </div>

          {/* System status pill */}
          <div className="flex items-center justify-between px-2 py-1.5 bg-[#131924] rounded-md border border-[#1f283a] text-[10px] text-neutral-400">
            <span className="flex items-center gap-1.5">
              <Database className="w-3 h-3 text-brand-400" />
              <span>FAISS: {healthInfo?.vectors_count || 0} vectors</span>
            </span>
            <span className="flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${healthInfo?.claude_configured ? 'bg-brand-500' : 'bg-amber-500'}`} />
              <span>{healthInfo?.claude_configured ? 'Claude Ready' : 'API Key Req.'}</span>
            </span>
          </div>
        </div>
      </aside>
    </>
  );
}
