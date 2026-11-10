import React, { useState } from 'react';
import { User, Bot, Copy, Check, Sparkles, BookOpen } from 'lucide-react';
import SourceCitation from './SourceCitation';

export default function MessageBubble({ message, onOpenCitation }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Basic markdown-like formatting helper for clean display without huge bulky external dependencies
  const formatContent = (content) => {
    if (!content) return null;

    const lines = content.split('\n');
    return lines.map((line, idx) => {
      // Heading ###
      if (line.startsWith('### ')) {
        return <h3 key={idx} className="text-sm font-bold text-white mt-3 mb-1">{line.replace('### ', '')}</h3>;
      }
      // Heading ##
      if (line.startsWith('## ')) {
        return <h2 key={idx} className="text-base font-bold text-white mt-4 mb-2">{line.replace('## ', '')}</h2>;
      }
      // Heading #
      if (line.startsWith('# ')) {
        return <h1 key={idx} className="text-lg font-bold text-white mt-4 mb-2">{line.replace('# ', '')}</h1>;
      }
      // Bullet list items
      if (line.trim().startsWith('- ') || line.trim().startsWith('* ') || line.trim().startsWith('• ')) {
        const itemText = line.trim().replace(/^[-*•]\s+/, '');
        return (
          <li key={idx} className="ml-4 list-disc text-neutral-200 text-sm leading-relaxed mb-1">
            {renderInlineMarkdown(itemText)}
          </li>
        );
      }
      // Numbered list items
      const numMatch = line.trim().match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <li key={idx} className="ml-4 list-decimal text-neutral-200 text-sm leading-relaxed mb-1">
            {renderInlineMarkdown(numMatch[2])}
          </li>
        );
      }
      // Empty line
      if (!line.trim()) {
        return <div key={idx} className="h-2" />;
      }
      // Regular paragraph
      return (
        <p key={idx} className="text-sm text-neutral-200 leading-relaxed mb-1.5">
          {renderInlineMarkdown(line)}
        </p>
      );
    });
  };

  const renderInlineMarkdown = (text) => {
    // Bold **text**
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="bg-[#1f293d] text-[#7ee787] px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
      }
      return part;
    });
  };

  return (
    <div className={`py-4 px-4 sm:px-6 transition-colors ${isUser ? 'bg-transparent' : 'bg-[#141b27]/60 border-y border-[#1f283a]'}`}>
      <div className="max-w-3xl mx-auto flex gap-3.5">
        {/* Avatar */}
        <div className="shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-brand-600 to-emerald-400 flex items-center justify-center text-white shadow-md">
              <User className="w-4 h-4" />
            </div>
          ) : (
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md">
              <Bot className="w-4 h-4" />
            </div>
          )}
        </div>

        {/* Message Body */}
        <div className="flex-1 overflow-hidden">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-neutral-300">
              {isUser ? 'You' : 'PDF Intelligence Assistant'}
            </span>

            {!isUser && (
              <button
                onClick={handleCopy}
                className="text-neutral-500 hover:text-neutral-300 transition p-1 rounded flex items-center gap-1 text-[11px]"
                title="Copy response"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-brand-400" />
                    <span className="text-brand-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            )}
          </div>

          <div className="prose-container break-words">
            {formatContent(message.content)}
          </div>

          {/* Citations Section */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-[#232d3f]">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-400 mb-2">
                <BookOpen className="w-3.5 h-3.5 text-brand-400" />
                <span>Verified PDF Sources & Page References:</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {message.citations.map((citation, idx) => (
                  <SourceCitation
                    key={citation.chunk_id || idx}
                    citation={citation}
                    onOpenCitation={onOpenCitation}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
