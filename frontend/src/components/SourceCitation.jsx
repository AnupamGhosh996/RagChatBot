import React, { useState } from 'react';
import { FileText, ExternalLink, ChevronDown, ChevronUp, Bookmark } from 'lucide-react';

export default function SourceCitation({ citation, onOpenCitation }) {
  const [expanded, setExpanded] = useState(false);

  const handleClick = (e) => {
    e.stopPropagation();
    if (onOpenCitation) {
      onOpenCitation(citation);
    }
  };

  return (
    <div className="inline-block m-1 text-xs">
      <div 
        className="flex items-center gap-1.5 bg-[#1c2331] hover:bg-[#252f42] border border-[#303d52] hover:border-brand-500/60 text-[#c9d1d9] rounded-lg px-2.5 py-1.5 transition-all duration-150 cursor-pointer group shadow-sm"
        onClick={handleClick}
        title={`Click to open ${citation.document_name} at Page ${citation.page_number}`}
      >
        <FileText className="w-3.5 h-3.5 text-brand-500 shrink-0" />
        <span className="font-medium text-white truncate max-w-[140px]">
          {citation.document_name}
        </span>
        <span className="bg-brand-500/15 text-brand-400 font-semibold px-1.5 py-0.5 rounded text-[10px] shrink-0 border border-brand-500/30">
          Page {citation.page_number}
        </span>
        
        {citation.score && (
          <span className="text-[10px] text-neutral-400 hidden sm:inline" title="Cosine Similarity Score">
            {(citation.score * 100).toFixed(0)}% match
          </span>
        )}

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-neutral-400 hover:text-white p-0.5 rounded ml-0.5"
          title="Toggle text snippet"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>

        <ExternalLink className="w-3 h-3 text-neutral-400 group-hover:text-brand-400 shrink-0 ml-0.5" />
      </div>

      {expanded && citation.snippet && (
        <div className="mt-1.5 p-2 bg-[#121721] border border-[#2b3547] rounded-md text-[11px] text-neutral-300 max-w-md shadow-md animate-fadeIn">
          <div className="flex items-center justify-between pb-1 mb-1 border-b border-[#252f40] text-[10px] text-neutral-400">
            <span className="flex items-center gap-1 font-semibold text-brand-400">
              <Bookmark className="w-3 h-3" /> Excerpt from Page {citation.page_number}
            </span>
            <button 
              onClick={handleClick} 
              className="text-brand-400 hover:underline flex items-center gap-1"
            >
              Jump to PDF <ExternalLink className="w-2.5 h-2.5" />
            </button>
          </div>
          <p className="italic leading-relaxed text-neutral-300">
            "{citation.snippet}"
          </p>
        </div>
      )}
    </div>
  );
}
