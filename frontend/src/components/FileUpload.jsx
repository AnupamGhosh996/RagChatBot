import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';
import { api } from '../services/api';

export default function FileUpload({ onUploadSuccess, onClose }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const processFiles = async (files) => {
    setError(null);
    const validFiles = [];

    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      if (!f.name.toLowerCase().endsWith('.pdf')) {
        setError(`"${f.name}" is not a PDF file. Please upload PDF documents only.`);
        return;
      }
      if (f.size > 50 * 1024 * 1024) {
        setError(`"${f.name}" exceeds the maximum allowed file size of 50MB.`);
        return;
      }
      validFiles.push(f);
    }

    if (validFiles.length === 0) return;

    try {
      setIsProcessing(true);
      setCurrentStep('1/4: Uploading PDF file(s)...');
      setUploadProgress(20);

      // Simulated pipeline progress indicators for transparent UX
      const timer1 = setTimeout(() => {
        setCurrentStep('2/4: Extracting text & preserving page numbers...');
        setUploadProgress(50);
      }, 700);

      const timer2 = setTimeout(() => {
        setCurrentStep('3/4: Creating recursive chunks (~1000 chars)...');
        setUploadProgress(75);
      }, 1500);

      const timer3 = setTimeout(() => {
        setCurrentStep('4/4: Generating Sentence Transformer embeddings & indexing in FAISS...');
        setUploadProgress(90);
      }, 2300);

      const response = await api.uploadPDFs(validFiles, (progress) => {
        if (progress < 90) setUploadProgress(Math.max(progress, 20));
      });

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);

      setUploadProgress(100);
      setCurrentStep('Complete! Vectors stored in FAISS.');

      setTimeout(() => {
        setIsProcessing(false);
        if (onUploadSuccess) {
          onUploadSuccess(response.documents);
        }
        if (onClose) {
          onClose();
        }
      }, 800);

    } catch (err) {
      setIsProcessing(false);
      setUploadProgress(0);
      const detail = err.response?.data?.detail || err.message || 'Failed to process document.';
      setError(detail);
    }
  };

  return (
    <div className="bg-[#141b27] border border-[#252f42] rounded-xl p-5 shadow-xl relative max-w-lg w-full">
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-neutral-400 hover:text-white p-1 rounded-md"
        >
          <X className="w-4 h-4" />
        </button>
      )}

      <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
        <UploadCloud className="w-4 h-4 text-brand-500" />
        Upload PDF Documents
      </h3>
      <p className="text-xs text-neutral-400 mb-4">
        Supports multiple PDF files up to 50MB. Text will be chunked, embedded with MiniLM, and indexed in FAISS.
      </p>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isProcessing && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-brand-500 bg-brand-500/10'
            : 'border-[#2e3b52] hover:border-[#405273] bg-[#0f141f]'
        } ${isProcessing ? 'pointer-events-none opacity-60' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={handleFileInput}
          disabled={isProcessing}
        />

        <div className="flex flex-col items-center justify-center gap-2">
          <div className="w-10 h-10 rounded-full bg-[#1b2434] flex items-center justify-center text-brand-400 shadow-inner">
            <UploadCloud className="w-5 h-5" />
          </div>
          <p className="text-xs font-medium text-white">
            Drag & drop PDF files here, or <span className="text-brand-400 underline">browse files</span>
          </p>
          <p className="text-[11px] text-neutral-500">
            Page numbers and exact source references will be preserved
          </p>
        </div>
      </div>

      {/* Progress and status */}
      {isProcessing && (
        <div className="mt-4 bg-[#0e131d] border border-[#232d3f] p-3 rounded-lg animate-fadeIn">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="flex items-center gap-2 text-neutral-300">
              <Loader2 className="w-3.5 h-3.5 text-brand-500 animate-spin" />
              {currentStep}
            </span>
            <span className="text-brand-400 font-semibold">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-[#1c2433] rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-brand-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div className="mt-4 p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-xs text-red-300 flex items-start gap-2 animate-shake">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block text-red-200">Upload Failed</span>
            {error}
          </div>
        </div>
      )}
    </div>
  );
}
