import React, { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, Download, FileText, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { api } from '../services/api';

export default function PDFViewer({ document, initialPage = 1, onClose }) {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (initialPage) {
      setCurrentPage(initialPage);
    }
  }, [initialPage, document?.id]);

  if (!document) return null;

  const pdfUrl = `/api/documents/${document.id}/file#page=${currentPage}&zoom=${zoom}`;

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const handleNextPage = () => {
    if (!document.page_count || currentPage < document.page_count) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const handlePageInputChange = (e) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val) && val >= 1 && (!document.page_count || val <= document.page_count)) {
      setCurrentPage(val);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#111622] border-l border-[#263042] w-full md:w-[480px] lg:w-[560px] xl:w-[640px] shrink-0 transition-all duration-300 z-20 shadow-2xl">
      {/* Top Controls Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#161d2a] border-b border-[#263042]">
        <div className="flex items-center gap-2 overflow-hidden mr-2">
          <FileText className="w-4 h-4 text-brand-500 shrink-0" />
          <span className="text-xs font-semibold text-white truncate max-w-[180px] lg:max-w-[240px]" title={document.original_name}>
            {document.original_name}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {/* Page navigation */}
          <div className="flex items-center bg-[#0d121b] border border-[#263042] rounded-md px-1.5 py-0.5 text-xs text-neutral-300">
            <button
              onClick={handlePrevPage}
              disabled={currentPage <= 1}
              className="p-1 text-neutral-400 hover:text-white disabled:opacity-30 disabled:hover:text-neutral-400"
              title="Previous Page"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <div className="flex items-center gap-1 px-1.5">
              <span>Page</span>
              <input
                type="number"
                min="1"
                max={document.page_count || 9999}
                value={currentPage}
                onChange={handlePageInputChange}
                className="w-10 bg-[#161d2a] border border-[#303d52] rounded text-center text-xs text-white py-0.5 focus:outline-none focus:border-brand-500"
              />
              <span className="text-neutral-500">/ {document.page_count || '?'}</span>
            </div>
            <button
              onClick={handleNextPage}
              disabled={document.page_count && currentPage >= document.page_count}
              className="p-1 text-neutral-400 hover:text-white disabled:opacity-30 disabled:hover:text-neutral-400"
              title="Next Page"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Download */}
          <a
            href={`/api/documents/${document.id}/file`}
            download={document.original_name}
            className="p-1.5 text-neutral-400 hover:text-white hover:bg-[#20293a] rounded-md transition"
            title="Download PDF"
          >
            <Download className="w-4 h-4" />
          </a>

          {/* Close */}
          <button
            onClick={onClose}
            className="p-1.5 text-neutral-400 hover:text-white hover:bg-[#20293a] rounded-md transition ml-1"
            title="Close Viewer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Citations jump notification pill */}
      <div className="bg-[#192233] px-3 py-1.5 border-b border-[#263042] text-[11px] text-neutral-400 flex items-center justify-between">
        <span>Viewing page cited in answers: <strong className="text-brand-400">Page {currentPage}</strong></span>
        <span className="text-[10px] text-neutral-500">Built-in PDF Preview</span>
      </div>

      {/* PDF Viewport iframe */}
      <div className="flex-1 bg-[#0b0e14] relative">
        <iframe
          key={`${document.id}-page-${currentPage}`}
          src={pdfUrl}
          title={document.original_name}
          className="w-full h-full border-none"
        />
      </div>
    </div>
  );
}
