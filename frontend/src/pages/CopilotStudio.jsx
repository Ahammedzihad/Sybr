import React, { useState, useEffect, useRef } from 'react';
import { 
  Bot, 
  Sparkles, 
  Image as ImageIcon, 
  UploadCloud, 
  Check, 
  Copy, 
  ShieldAlert, 
  RefreshCw, 
  X, 
  Clock, 
  HelpCircle,
  Laptop,
  CreditCard,
  Lock,
  ChevronRight,
  ListTodo,
  FileText
} from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { PriorityBadge } from '../components/Badges';
import { diagnoseIssue, fetchCopilotHistory } from '../api';

const PRESETS = [
  {
    label: 'Payment Gateway 3DS Timeout',
    category: 'Payment & Billing',
    icon: CreditCard,
    message: 'Customer reports card was declined during 3D-Secure checkout verification, but their bank shows a pending hold for $149.00.',
    image_name: 'checkout_declined_error.png',
    image_data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
  },
  {
    label: 'Phishing Security Alert',
    category: 'Security Alert',
    icon: ShieldAlert,
    message: 'URGENT: Received an email asking to confirm our corporate master password immediately via paypa1-auth.example.com to avoid account suspension.',
    image_name: 'spoofed_login_attempt.png',
    image_data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
  },
  {
    label: '500 Server Exception on Reports',
    category: 'Technical Issue',
    icon: Laptop,
    message: 'When clicking Export Monthly Reports, the screen turns blank with "Internal Server Error 500: Database Connection Pool Exhausted".',
    image_name: 'stack_trace_500.png',
    image_data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
  },
  {
    label: 'Account Lockout & MFA Loop',
    category: 'Account Access',
    icon: Lock,
    message: 'User entered wrong password 3 times and is now stuck in an infinite SMS OTP loop that says "Too many attempts. Contact Administrator".',
    image_name: 'mfa_lockout_screen.png',
    image_data: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
  }
];

export default function CopilotStudio() {
  const [message, setMessage] = useState('');
  const [imageData, setImageData] = useState(null);
  const [imageName, setImageName] = useState(null);
  const [channel, setChannel] = useState('chat');
  const [loading, setLoading] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [checkedSteps, setCheckedSteps] = useState({});
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await fetchCopilotHistory(10);
      setHistory(data || []);
    } catch (err) {
      console.warn('Could not load history:', err);
    }
  };

  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          e.preventDefault();
          const file = items[i].getAsFile();
          if (file) {
            processImageFile(file);
          }
          break;
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, []);

  const processImageFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setImageData(e.target.result);
      setImageName(file.name || 'clipboard-screenshot.png');
    };
    reader.readAsDataURL(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      processImageFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      processImageFile(file);
    }
  };

  const removeImage = () => {
    setImageData(null);
    setImageName(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDiagnose = async (e) => {
    if (e) e.preventDefault();
    if (!message.trim() && !imageData) return;

    try {
      setLoading(true);
      const result = await diagnoseIssue({
        message: message.trim() || undefined,
        image_data: imageData || undefined,
        image_name: imageName || undefined,
        channel: channel || 'chat',
      });
      setDiagnosis(result);
      setCheckedSteps({});
      loadHistory();
    } catch (err) {
      alert('Diagnosis error: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const toggleStep = (idx) => {
    setCheckedSteps(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const copyResponse = () => {
    if (!diagnosis?.suggested_response) return;
    navigator.clipboard.writeText(diagnosis.suggested_response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  const loadPreset = (preset) => {
    setMessage(preset.message);
    setImageName(preset.image_name);
    setImageData(preset.image_data);
    setChannel('chat');
  };

  const selectHistoryItem = (item) => {
    setDiagnosis(item);
    setMessage(item.raw_message || '');
    setImageName(item.image_name || null);
    setImageData(null);
    setCheckedSteps({});
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      
      {/* Top Header & Context Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-200/70">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-neutral-900 text-white shadow-xs">
              <Bot className="w-4 h-4 text-emerald-400" />
            </span>
            <h1 className="text-xl font-semibold text-neutral-900 tracking-tight font-sans">
              AI Issue Diagnosis & Resolution Copilot
            </h1>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/80">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Gemini Vision Ready
            </span>
          </div>
          <p className="text-xs text-neutral-500 mt-1 max-w-2xl">
            Submit customer messages, error logs, or paste screenshots directly (⌘V). The Copilot identifies root causes, detects phishing threats, and builds step-by-step resolution checklists.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button 
            variant="secondary" 
            size="sm"
            icon={RefreshCw}
            onClick={() => {
              setMessage('');
              removeImage();
              setDiagnosis(null);
              setCheckedSteps({});
            }}
          >
            Reset Form
          </Button>
        </div>
      </div>

      {/* Quick Scenario Presets */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-neutral-600 uppercase tracking-wider">
            Quick Demonstration Presets
          </span>
          <span className="text-[11px] text-neutral-400">Click any to auto-fill input</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {PRESETS.map((p, idx) => {
            const Icon = p.icon;
            return (
              <button
                key={idx}
                onClick={() => loadPreset(p)}
                className="text-left p-3 rounded-xl bg-white border border-neutral-200/80 hover:border-neutral-300 hover:shadow-xs transition-all duration-150 flex items-start gap-2.5 group cursor-pointer"
              >
                <div className="p-2 rounded-lg bg-neutral-100 text-neutral-700 group-hover:bg-neutral-900 group-hover:text-white transition-colors shrink-0">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-neutral-900 truncate group-hover:text-neutral-950 font-sans">
                    {p.label}
                  </p>
                  <p className="text-[11px] text-neutral-500 truncate mt-0.5">
                    {p.category}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main 2-Column Studio Grid: Left Composer, Right Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Multimodal Input Composer (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card 
            title="Issue Composer"
            subtitle="Describe the issue and attach supporting screenshots"
            icon={Sparkles}
            className="shadow-xs border-neutral-200/80"
          >
            <form onSubmit={handleDiagnose} className="space-y-4">
              
              {/* Channel Selector */}
              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1.5">
                  Communication Channel
                </label>
                <div className="grid grid-cols-4 gap-1.5 bg-neutral-100/80 p-1 rounded-lg border border-neutral-200/60">
                  {['chat', 'email', 'ticket', 'app'].map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setChannel(c)}
                      className={`text-xs capitalize py-1 px-2 rounded-md font-medium transition-all ${
                        channel === c 
                          ? 'bg-white text-neutral-900 shadow-xs border border-neutral-200/60' 
                          : 'text-neutral-600 hover:text-neutral-900'
                      }`}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Message Input Textarea */}
              <div>
                <label className="block text-xs font-medium text-neutral-700 mb-1.5">
                  Customer Message / Issue Description
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Paste user message, error traceback, or issue description..."
                  rows={4}
                  className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-xs text-neutral-900 placeholder:text-neutral-400 focus:border-neutral-900 focus:outline-none focus:ring-1 focus:ring-neutral-900 transition-all font-sans"
                />
              </div>

              {/* Visual Asset Attachment & Drop Zone */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-medium text-neutral-700 flex items-center gap-1.5">
                    <ImageIcon className="w-3.5 h-3.5 text-neutral-500" />
                    Screenshot / Error Capture
                  </label>
                  <span className="text-[11px] text-neutral-400 font-mono">
                    Paste ⌘V supported
                  </span>
                </div>

                {imageData ? (
                  /* Attached Image Preview */
                  <div className="relative rounded-xl border border-neutral-200 bg-neutral-50 p-2.5 flex items-center gap-3">
                    <div className="w-14 h-14 rounded-lg overflow-hidden bg-neutral-200 border border-neutral-300 shrink-0 flex items-center justify-center">
                      <img 
                        src={imageData} 
                        alt="Attachment preview" 
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-neutral-900 truncate">
                        {imageName || 'attached_image.png'}
                      </p>
                      <span className="inline-flex items-center gap-1 mt-1 text-[11px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded font-medium border border-emerald-200/60">
                        <Check className="w-3 h-3" /> Visual Ready for Gemini
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={removeImage}
                      className="p-1.5 text-neutral-400 hover:text-neutral-700 hover:bg-neutral-200 rounded-lg transition-colors"
                      title="Remove image"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  /* Drag and Drop Zone */
                  <div
                    onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                    onDragLeave={() => setIsDragOver(false)}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-150 ${
                      isDragOver 
                        ? 'border-neutral-900 bg-neutral-100/70' 
                        : 'border-neutral-200/90 hover:border-neutral-400 hover:bg-neutral-50'
                    }`}
                  >
                    <input 
                      ref={fileInputRef}
                      type="file" 
                      accept="image/*" 
                      className="hidden" 
                      onChange={handleFileChange}
                    />
                    <div className="flex flex-col items-center justify-center gap-1.5">
                      <div className="p-2 rounded-full bg-neutral-100 text-neutral-600">
                        <UploadCloud className="w-5 h-5" />
                      </div>
                      <p className="text-xs font-medium text-neutral-800">
                        Click to upload or drag & drop image
                      </p>
                      <p className="text-[11px] text-neutral-400">
                        Or press <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-neutral-100 border border-neutral-200 rounded text-neutral-600">⌘V</kbd> anywhere to paste from clipboard
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Submit Button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                disabled={!message.trim() && !imageData}
                icon={Sparkles}
                className="w-full font-medium tracking-tight"
              >
                {loading ? 'Analyzing with Gemini Vision...' : 'Diagnose & Generate Help'}
              </Button>
            </form>
          </Card>

          {/* Recent History Mini-Drawer */}
          {history.length > 0 && (
            <Card 
              title="Recent Copilot Sessions" 
              subtitle="Past diagnostic sessions in this workspace"
              icon={Clock}
              bodyClassName="p-2 space-y-1.5"
            >
              {history.slice(0, 5).map((h) => (
                <button
                  key={h.session_id}
                  onClick={() => selectHistoryItem(h)}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between gap-3 text-xs cursor-pointer ${
                    diagnosis?.session_id === h.session_id
                      ? 'bg-neutral-900 text-white border-neutral-900'
                      : 'bg-white hover:bg-neutral-50 text-neutral-800 border-neutral-200/70'
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-medium truncate">{h.issue_title}</p>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px] opacity-75">
                      <span>{h.category}</span>
                      <span>•</span>
                      <span>{h.severity}</span>
                      {h.is_threat && (
                        <span className="text-rose-400 font-semibold">• Phish</span>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 opacity-50 shrink-0" />
                </button>
              ))}
            </Card>
          )}
        </div>

        {/* Right Column: Diagnostic Dossier & Resolution Plan (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {diagnosis ? (
            <div className="space-y-4">
              
              {/* Threat Alert Banner if Security Risk Detected */}
              {diagnosis.is_threat && (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start gap-3 shadow-xs">
                  <div className="p-1.5 rounded-lg bg-rose-600 text-white shrink-0 mt-0.5">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold tracking-tight">
                        Critical Security Threat Identified
                      </h3>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-200 text-rose-800">
                        Phishing / Credential Attack
                      </span>
                    </div>
                    <p className="text-xs text-rose-800 mt-1 leading-relaxed">
                      {diagnosis.threat_details || 'The interaction or visual attachment contains active phishing indicators or suspicious authorization lures.'}
                    </p>
                  </div>
                </div>
              )}

              {/* Main Diagnostic Findings Card */}
              <Card
                title={diagnosis.issue_title}
                subtitle={`Session ID: ${diagnosis.session_id} • Analyzed via ${diagnosis.ai_mode} (${diagnosis.processing_ms}ms)`}
                action={
                  <div className="flex items-center gap-2">
                    <PriorityBadge level={diagnosis.severity} />
                    <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-neutral-100 text-neutral-700 border border-neutral-200">
                      {diagnosis.category}
                    </span>
                  </div>
                }
              >
                <div className="space-y-4">
                  
                  {/* Root Cause Analysis */}
                  <div>
                    <h4 className="text-xs font-semibold text-neutral-800 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-neutral-900"></span>
                      Root Cause Analysis
                    </h4>
                    <p className="text-xs text-neutral-700 leading-relaxed bg-neutral-50 p-3 rounded-lg border border-neutral-200/70 font-sans">
                      {diagnosis.root_cause}
                    </p>
                  </div>

                  {/* Visual Findings if Available */}
                  {diagnosis.visual_findings && diagnosis.visual_findings.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-neutral-800 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                        <ImageIcon className="w-3.5 h-3.5 text-neutral-600" />
                        Visual & Forensic Findings
                      </h4>
                      <ul className="space-y-1.5">
                        {diagnosis.visual_findings.map((item, idx) => (
                          <li key={idx} className="text-xs text-neutral-600 flex items-start gap-2 bg-neutral-50/60 px-3 py-2 rounded-md border border-neutral-100">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0 mt-1.5"></span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Troubleshooting Step-by-Step Checklist */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-xs font-semibold text-neutral-800 uppercase tracking-wider flex items-center gap-1.5">
                        <ListTodo className="w-3.5 h-3.5 text-neutral-700" />
                        Actionable Troubleshooting Steps
                      </h4>
                      <span className="text-[11px] text-neutral-400">
                        {Object.values(checkedSteps).filter(Boolean).length} / {diagnosis.troubleshooting_steps.length} verified
                      </span>
                    </div>

                    <div className="space-y-2">
                      {diagnosis.troubleshooting_steps.map((step, idx) => {
                        const isDone = Boolean(checkedSteps[idx]);
                        return (
                          <div 
                            key={idx}
                            onClick={() => toggleStep(idx)}
                            className={`p-3 rounded-xl border transition-all flex items-start gap-3 cursor-pointer select-none ${
                              isDone 
                                ? 'bg-emerald-50/50 border-emerald-200 text-neutral-500' 
                                : 'bg-white border-neutral-200/80 hover:border-neutral-300 text-neutral-800 shadow-xs'
                            }`}
                          >
                            <div className={`w-4 h-4 rounded mt-0.5 flex items-center justify-center border transition-colors shrink-0 ${
                              isDone 
                                ? 'bg-emerald-600 border-emerald-600 text-white' 
                                : 'border-neutral-300 bg-white'
                            }`}>
                              {isDone && <Check className="w-3 h-3" />}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className={`text-xs font-medium leading-relaxed ${isDone ? 'line-through opacity-70' : ''}`}>
                                <span className="font-mono text-neutral-400 mr-1.5">0{idx + 1}.</span>
                                {step}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Customer Support Response Draft */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <h4 className="text-xs font-semibold text-neutral-800 uppercase tracking-wider flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-neutral-600" />
                        Ready-to-Copy Customer Response Draft
                      </h4>
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={copied ? Check : Copy}
                        onClick={copyResponse}
                        className={copied ? 'text-emerald-700 border-emerald-300 bg-emerald-50' : ''}
                      >
                        {copied ? 'Copied to Clipboard!' : 'Copy Response'}
                      </Button>
                    </div>
                    <div className="bg-neutral-900 text-neutral-100 p-4 rounded-xl text-xs leading-relaxed font-sans shadow-inner select-text">
                      {diagnosis.suggested_response}
                    </div>
                  </div>

                  {/* Prevention Tip */}
                  {diagnosis.prevention_tip && (
                    <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 flex items-start gap-2.5">
                      <HelpCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-800 block">
                          Long-Term Prevention Tip
                        </span>
                        <p className="text-xs text-amber-900/90 mt-0.5 leading-relaxed">
                          {diagnosis.prevention_tip}
                        </p>
                      </div>
                    </div>
                  )}

                </div>
              </Card>
            </div>
          ) : (
            /* Empty State Placeholder */
            <Card className="border-dashed border-2 border-neutral-200/90 bg-neutral-50/50 p-12 text-center">
              <div className="flex flex-col items-center justify-center max-w-sm mx-auto">
                <div className="w-12 h-12 rounded-2xl bg-neutral-100 border border-neutral-200 flex items-center justify-center text-neutral-400 mb-3">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-semibold text-neutral-800 font-sans">
                  Diagnostic Dossier Ready
                </h3>
                <p className="text-xs text-neutral-500 mt-1 leading-relaxed">
                  Type an issue description, attach a screenshot, or click one of the quick presets on the left to begin diagnosis.
                </p>
                <div className="mt-4 p-2.5 bg-white border border-neutral-200/80 rounded-lg text-left w-full text-[11px] text-neutral-600 space-y-1">
                  <div className="font-medium text-neutral-900">Multimodal Capabilities:</div>
                  <div>• Optical character & error code recognition</div>
                  <div>• Phishing URL & spoofed domain threat check</div>
                  <div>• Tailored step-by-step resolution checklist</div>
                  <div>• One-click customer support reply draft</div>
                </div>
              </div>
            </Card>
          )}
        </div>

      </div>

    </div>
  );
}
