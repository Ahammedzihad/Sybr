import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  FileCheck, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle2, 
  FileText, 
  FileSpreadsheet, 
  X 
} from 'lucide-react';
import { uploadDatasetFile, pollJobStatus } from '../api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

export default function Upload() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const startUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    try {
      const initRes = await uploadDatasetFile(file);
      const jobId = initRes.job_id;
      setJob({ job_id: jobId, status: 'processing', total: initRes.total || 0, processed: 0 });

      // Poll job status until completed
      const pollInterval = setInterval(async () => {
        try {
          const status = await pollJobStatus(jobId);
          setJob(status);
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(pollInterval);
            setUploading(false);
            if (status.status === 'completed') {
              setTimeout(() => navigate('/conversations'), 1500);
            }
          }
        } catch (pollErr) {
          clearInterval(pollInterval);
          setUploading(false);
          setError('Failed to poll background processing status.');
        }
      }, 1000);

    } catch (err) {
      setUploading(false);
      setError(err.message || 'Failed to upload dataset.');
    }
  };

  const percent = job?.total > 0 ? Math.round((job.processed / job.total) * 100) : 0;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-fade-in">
      
      {/* Header */}
      <div className="border-b border-neutral-200/80 pb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-neutral-900 tracking-tight flex items-center gap-2.5 font-sans">
          <UploadCloud className="w-5 h-5 text-neutral-900" />
          Batch Ingestion & File Upload
        </h1>
        <p className="text-neutral-500 text-xs sm:text-sm mt-0.5">
          Ingest multi-turn customer conversations from CSV or JSON with automatic schema normalization
        </p>
      </div>

      {/* Drag & Drop Card */}
      <Card>
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-150 ${
            dragOver
              ? 'border-neutral-900 bg-neutral-100/60'
              : 'border-neutral-200 hover:border-neutral-400 bg-neutral-50/40 hover:bg-neutral-50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv,.json"
            className="hidden"
          />
          <div className="w-12 h-12 rounded-xl bg-neutral-100 border border-neutral-200 text-neutral-800 flex items-center justify-center mx-auto mb-3 shadow-xs">
            <UploadCloud className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-neutral-900 mb-1 font-sans">
            Drop CSV or JSON dataset here
          </h3>
          <p className="text-xs text-neutral-500 mb-3 max-w-sm mx-auto">
            Click to browse your local files. Flexible column detection auto-maps your headers.
          </p>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-md bg-neutral-100 border border-neutral-200/60 text-[10px] text-neutral-600 font-mono font-medium">
            Supported formats: .csv, .json (max 50MB)
          </div>
        </div>

        {/* Selected File Details */}
        {file && (
          <div className="mt-4 p-3 rounded-lg bg-neutral-50 border border-neutral-200/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-white text-[#007aff] shadow-sm border border-black/[0.06]">
                {file.name.endsWith('.csv') ? <FileSpreadsheet className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
              </div>
              <div>
                <p className="text-xs font-semibold text-[#1d1d1f] truncate max-w-xs sm:max-w-md">{file.name}</p>
                <p className="text-[11px] text-[#59595e] font-mono">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            {!uploading && (
              <button
                onClick={(e) => { e.stopPropagation(); setFile(null); setJob(null); }}
                className="p-1 rounded-full text-[#59595e] hover:text-[#1d1d1f] hover:bg-black/[0.06] transition"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* Action Button */}
        {file && !job && (
          <div className="mt-4 flex justify-end">
            <Button
              variant="primary"
              size="md"
              onClick={startUpload}
              loading={uploading}
              icon={UploadCloud}
            >
              Start Batch Ingestion
            </Button>
          </div>
        )}

        {/* Job Processing Progress Bar */}
        {job && (
          <div className="mt-6 p-4 rounded-2xl bg-black/[0.02] border border-black/[0.06] space-y-3">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                {job.status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-[#1b6d31]" />
                ) : (
                  <RefreshCw className="w-4 h-4 text-[#007aff] animate-spin" />
                )}
                <span className="font-semibold text-[#1d1d1f]">
                  {job.status === 'completed' ? 'Processing Complete!' : 'Processing Conversations...'}
                </span>
              </div>
              <span className="font-mono text-[#59595e] font-medium">
                {job.processed} / {job.total} records ({percent}%)
              </span>
            </div>

            <div className="w-full bg-black/[0.06] rounded-full h-2 overflow-hidden">
              <div
                className="bg-[#007aff] h-2 rounded-full transition-all duration-300"
                style={{ width: `${percent}%` }}
              />
            </div>

            {job.status === 'completed' && (
              <p className="text-xs text-[#1b6d31] font-semibold">
                ✓ Successfully indexed into database. Redirecting to inbox...
              </p>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3.5 rounded-2xl bg-[#ff3b30]/10 border border-[#ff3b30]/20 text-[#b81414] text-xs font-medium flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-[#b81414]" />
            <span>{error}</span>
          </div>
        )}
      </Card>

      {/* Ingestion Specification Guide */}
      <Card title="Format Guidelines & Column Detection" subtitle="Built-in fuzzy column matching automatically maps your schema">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-[#3c3c43]">
          <div className="p-4 rounded-xl bg-black/[0.02] border border-black/[0.05] space-y-2">
            <div className="font-semibold text-[#1d1d1f] flex items-center gap-1.5">
              <FileSpreadsheet className="w-4 h-4 text-[#007aff]" />
              CSV Requirements
            </div>
            <p className="text-[#59595e] text-[11px] leading-relaxed">
              Auto-detects column variations:
            </p>
            <ul className="list-disc list-inside space-y-1 text-[#59595e] font-mono text-[11px]">
              <li>Message: <span className="text-[#1d1d1f]">text, message, body, customer_issue</span></li>
              <li>Identifier: <span className="text-[#1d1d1f]">conversation_id, ticket_id, id</span></li>
              <li>Sender: <span className="text-[#1d1d1f]">sender, role, author</span></li>
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-black/[0.02] border border-black/[0.05] space-y-2">
            <div className="font-semibold text-[#1d1d1f] flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-[#007aff]" />
              JSON Requirements
            </div>
            <p className="text-[#59595e] text-[11px] leading-relaxed">
              Accepts arrays of interaction objects or multi-turn conversation objects with embedded message lists.
            </p>
            <div className="font-mono text-[11px] text-[#1d1d1f] bg-black/[0.03] p-2.5 rounded-lg border border-black/[0.05]">
              {"[{ \"conversation_id\": \"CS-01\", \"messages\": [...] }]"}
            </div>
          </div>
        </div>
      </Card>

    </div>
  );
}
