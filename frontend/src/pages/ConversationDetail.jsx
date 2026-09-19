import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  ShieldCheck, 
  ArrowLeft, 
  RefreshCw, 
  Trash2, 
  AlertTriangle, 
  FileText, 
  Mail, 
  Globe, 
  Paperclip,
  CheckCircle2,
  Clock,
  Sparkles,
  Info,
  Copy,
  Check,
  Edit3,
  Send,
  Lock,
  Flag,
  UserCheck,
  MessageSquare,
  X
} from 'lucide-react';
import { 
  fetchConversationById, 
  reanalyzeConversation, 
  deleteConversation,
  submitAdminReviewCorrection,
  updateAdminConversationStatus,
  addAdminInternalNote,
  requestHumanReview,
  generateDraftResponse,
  isAdmin
} from '../api';
import { PriorityBadge, RiskBadge, SentimentBadge, EmotionBadge, ResolutionBadge } from '../components/Badges';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { Skeleton } from '../components/ui/Skeleton';

const CANONICAL_CATEGORIES = [
  "Billing/Payment", "Account/Login", "Product Issue", "Delivery/Shipping",
  "Refund Request", "Subscription Issue", "Technical Problem", "Service Quality",
  "Security Concern", "Other"
];

const CANONICAL_ISSUE_LABELS = [
  "Login Failure", "Password Reset", "Payment Failure", "Duplicate Charge",
  "Refund Delay", "Delivery Delay", "Wrong/Damaged Item", "Order Not Confirmed",
  "Subscription Cancellation", "App Crash/Bug", "Service Outage", "Account Compromise",
  "Unauthorized Transaction", "Phishing Attempt", "Poor Support Experience", "Other"
];

export default function ConversationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Admin Review & Workflow State
  const adminMode = isAdmin();
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewCat, setReviewCat] = useState('');
  const [reviewLabel, setReviewLabel] = useState('');
  const [reviewPrio, setReviewPrio] = useState('');
  const [reviewRisk, setReviewRisk] = useState('');
  const [reviewStatus, setReviewStatus] = useState('');
  const [reviewReason, setReviewReason] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);

  // Internal Notes State
  const [noteText, setNoteText] = useState('');
  const [submittingNote, setSubmittingNote] = useState(false);

  // AI Draft Response State
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [draftData, setDraftData] = useState(null);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [copiedDraft, setCopiedDraft] = useState(false);

  const loadRecord = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchConversationById(id);
      setRecord(data);
      setReviewCat(data.category || 'Other');
      setReviewLabel(data.issue_label || 'Other');
      setReviewPrio(data.priority || 'Low');
      setReviewRisk(data.security?.risk_level || 'Low');
      setReviewStatus(data.resolution_status || 'Pending');
    } catch (err) {
      setError(err.message || 'Failed to load conversation details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecord();
  }, [id]);

  const handleCopyId = () => {
    if (!record) return;
    navigator.clipboard.writeText(record.conversation_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReanalyze = async () => {
    setReanalyzing(true);
    try {
      const updated = await reanalyzeConversation(id);
      setRecord(updated);
    } catch (err) {
      alert('Re-analysis failed: ' + err.message);
    } finally {
      setReanalyzing(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to permanently delete this conversation? (Privacy/GDPR compliance)')) return;
    try {
      await deleteConversation(id);
      navigate(adminMode ? '/admin/conversations' : '/conversations');
    } catch (err) {
      alert('Delete failed: ' + err.message);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    setSubmittingReview(true);
    try {
      const updated = await submitAdminReviewCorrection(id, {
        category: reviewCat,
        issue_label: reviewLabel,
        priority: reviewPrio,
        risk_level: reviewRisk,
        resolution_status: reviewStatus,
        reason: reviewReason || 'Manual administrative calibration',
      });
      setRecord(updated);
      setShowReviewModal(false);
    } catch (err) {
      alert('Correction submission failed: ' + err.message);
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleStatusChange = async (newStatus, newResolution) => {
    try {
      const updated = await updateAdminConversationStatus(id, {
        processing_status: newStatus,
        resolution_status: newResolution,
      });
      setRecord(updated);
    } catch (err) {
      alert('Status update failed: ' + err.message);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!noteText.trim()) return;
    setSubmittingNote(true);
    try {
      const newNote = await addAdminInternalNote(id, noteText.trim());
      setRecord((prev) => ({
        ...prev,
        internal_notes: [...(prev.internal_notes || []), newNote],
      }));
      setNoteText('');
    } catch (err) {
      alert('Failed to add internal note: ' + err.message);
    } finally {
      setSubmittingNote(false);
    }
  };

  const handleFlagReview = async () => {
    const reason = window.prompt('Enter reason for administrative review:', 'Ambiguous classification requiring supervisor review');
    if (!reason) return;
    try {
      const updated = await requestHumanReview(id, reason);
      setRecord(updated);
    } catch (err) {
      alert('Failed to flag for review: ' + err.message);
    }
  };

  const handleGenerateDraft = async () => {
    setShowDraftModal(true);
    setLoadingDraft(true);
    try {
      const draft = await generateDraftResponse(id);
      setDraftData(draft);
    } catch (err) {
      alert('Failed to generate draft response: ' + err.message);
    } finally {
      setLoadingDraft(false);
    }
  };

  const handleCopyDraft = () => {
    if (!draftData) return;
    navigator.clipboard.writeText(draftData.draft_response);
    setCopiedDraft(true);
    setTimeout(() => setCopiedDraft(false), 2000);
  };

  if (loading && !record) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-8 rounded-xl" />
          <div className="space-y-1.5">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-black/[0.08] rounded-2xl p-6 h-96 animate-pulse" />
          <div className="bg-white border border-black/[0.08] rounded-2xl p-6 h-96 animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 rounded-2xl bg-white border border-black/[0.08] text-center shadow-card">
        <div className="w-12 h-12 rounded-2xl bg-[#ff3b30]/10 border border-[#ff3b30]/20 flex items-center justify-center text-[#b81414] mx-auto mb-3.5">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-[#1d1d1f] mb-1">Record Not Found</h3>
        <p className="text-xs text-[#59595e] mb-5 leading-relaxed">{error}</p>
        <Link to={adminMode ? '/admin/conversations' : '/conversations'}>
          <Button variant="secondary" size="md">
            Back to Inbox
          </Button>
        </Link>
      </div>
    );
  }

  const { security, summary, messages } = record;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-fade-in text-left">
      
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-4">
        <div className="flex items-center gap-3">
          <Link
            to={adminMode ? '/admin/conversations' : '/conversations'}
            aria-label="Back to Conversations"
            className="p-1.5 rounded-md bg-white border border-neutral-200 hover:bg-neutral-50 text-neutral-700 transition shadow-xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleCopyId}
                className="font-mono text-xs font-medium px-2 py-0.5 rounded-md bg-neutral-100 text-neutral-800 border border-neutral-200/80 hover:bg-neutral-200/60 transition flex items-center gap-1.5"
                title="Click to copy ID"
              >
                {record.conversation_id}
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-neutral-400" />}
              </button>
              <span className="text-xs text-neutral-500 font-mono font-medium uppercase">[{record.channel || 'ticket'}]</span>
              <span className="text-xs text-neutral-400">• {new Date(record.created_at).toLocaleString()}</span>
              {record.is_human_reviewed && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                  <UserCheck className="w-3 h-3" />
                  Human Reviewed
                </span>
              )}
              {record.needs_human_review && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-1">
                  <Flag className="w-3 h-3" />
                  Needs Review
                </span>
              )}
            </div>
            <h1 className="text-lg sm:text-xl font-bold text-neutral-900 tracking-tight mt-1 font-sans">
              {record.customer_issue || record.issue_label}
            </h1>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
          {adminMode && (
            <>
              <button
                onClick={() => setShowReviewModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-neutral-900 text-white text-xs font-semibold hover:bg-neutral-800 transition shadow-xs"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Review & Correct</span>
              </button>
              <button
                onClick={handleGenerateDraft}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-indigo-200 bg-indigo-50/70 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                <span>Draft AI Reply</span>
              </button>
            </>
          )}

          <Button
            variant="secondary"
            size="sm"
            onClick={handleReanalyze}
            loading={reanalyzing}
            icon={RefreshCw}
          >
            Reanalyze
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={handleDelete}
            icon={Trash2}
          >
            Delete
          </Button>
        </div>
      </div>

      {/* Admin Operational Command Bar */}
      {adminMode && (
        <div className="bg-white p-3.5 rounded-2xl border border-neutral-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-semibold text-neutral-500 uppercase tracking-wider text-[10px]">
              Workflow Actions:
            </span>
            <div className="flex items-center gap-2">
              <span className="text-neutral-500">Status:</span>
              <select
                value={record.processing_status || 'AI Analyzed'}
                onChange={(e) => handleStatusChange(e.target.value, record.resolution_status)}
                className="px-2 py-1 bg-neutral-50 border border-neutral-200 rounded-lg text-xs font-medium outline-none"
              >
                <option value="AI Analyzed">AI Analyzed</option>
                <option value="Needs Review">Needs Review</option>
                <option value="In Progress">In Progress</option>
                <option value="Escalated">Escalated</option>
                <option value="Human Reviewed">Human Reviewed</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-neutral-500">Resolution:</span>
              <select
                value={record.resolution_status || 'Pending'}
                onChange={(e) => handleStatusChange(record.processing_status, e.target.value)}
                className="px-2 py-1 bg-neutral-50 border border-neutral-200 rounded-lg text-xs font-medium outline-none"
              >
                <option value="Pending">Pending</option>
                <option value="Unresolved">Unresolved</option>
                <option value="Resolved">Resolved</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {!record.needs_human_review ? (
              <button
                onClick={handleFlagReview}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-amber-200 text-amber-700 bg-amber-50 hover:bg-amber-100 transition text-[11px] font-semibold"
              >
                <Flag className="w-3 h-3" />
                <span>Flag for Review</span>
              </button>
            ) : (
              <button
                onClick={() => handleStatusChange('Human Reviewed', record.resolution_status)}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-emerald-200 text-emerald-700 bg-emerald-50 hover:bg-emerald-100 transition text-[11px] font-semibold"
              >
                <CheckCircle2 className="w-3 h-3" />
                <span>Mark Review Complete</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Human Review Audit Comparison Banner */}
      {record.is_human_reviewed && record.human_overrides && (
        <div className="p-4 rounded-2xl border border-amber-200 bg-amber-50/60 text-xs space-y-2">
          <div className="flex items-center justify-between font-semibold text-amber-900">
            <span className="flex items-center gap-1.5 font-bold">
              <UserCheck className="w-4 h-4 text-amber-700" />
              Administrative Calibration Record (Ground Truth Audited)
            </span>
            <span className="text-[11px] text-amber-700 font-mono">
              Reviewed by {record.reviewed_by || 'Supervisor'} • {new Date(record.reviewed_at).toLocaleString()}
            </span>
          </div>
          <div className="text-amber-800">
            <span className="font-semibold">Review Justification: </span>
            <span>{record.human_overrides.last_correction?.reason || 'Manual calibration against enterprise support criteria.'}</span>
          </div>
          {record.human_overrides.original && (
            <div className="pt-2 border-t border-amber-200/80 text-[11px] text-amber-700 flex flex-wrap gap-4">
              <span>Original AI Category: <b className="font-mono">{record.human_overrides.original.category}</b></span>
              <span>Original Issue: <b className="font-mono">{record.human_overrides.original.issue_label}</b></span>
              <span>Original Priority: <b className="font-mono">{record.human_overrides.original.priority}</b></span>
            </div>
          )}
        </div>
      )}

      {/* Recommended Operational Action Banner */}
      <div className={`p-3.5 rounded-xl border flex items-start gap-3 shadow-xs ${
        security.threat_detected
          ? 'bg-rose-50/80 border-rose-200 text-rose-800'
          : 'bg-emerald-50/80 border-emerald-200 text-emerald-800'
      }`}>
        {security.threat_detected ? (
          <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
        ) : (
          <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        )}
        <div className="flex-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 mb-0.5">
            Recommended Security & Operational Action
          </div>
          <div className="text-sm font-semibold text-neutral-900">
            {security.recommended_action || "Standard customer support routing; no security escalation required."}
          </div>
        </div>
      </div>

      {/* Signature Dual Inspector Panes */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* PANEL 1: CUSTOMER SUPPORT INTELLIGENCE */}
        <Card 
          title="Customer Support Intelligence" 
          subtitle="Intent classification & resolution tracking"
          action={
            <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-lg bg-black/[0.04] text-[#59595e] border border-black/[0.06]">
              {record.ai_mode} ({record.processing_ms}ms)
            </span>
          }
        >
          <div className="space-y-5">
            {/* Meta Tags Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                <div className="text-[11px] text-[#59595e] mb-1 font-medium">Category</div>
                <span className="text-xs font-semibold text-[#6e21a8] bg-[#af52de]/12 border border-[#af52de]/25 px-2 py-0.5 rounded-lg inline-block">
                  {record.category}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                <div className="text-[11px] text-[#59595e] mb-1 font-medium">Controlled Tag</div>
                <span className="text-xs font-semibold text-[#007aff] bg-[#007aff]/10 border border-[#007aff]/20 px-2 py-0.5 rounded-lg inline-block">
                  {record.issue_label}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                <div className="text-[11px] text-[#59595e] mb-1 font-medium">Priority</div>
                <PriorityBadge level={record.priority} reason={record.priority_reason} />
              </div>

              <div className="p-3 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                <div className="text-[11px] text-[#59595e] mb-1 font-medium">Sentiment</div>
                <SentimentBadge sentiment={record.sentiment} />
              </div>

              <div className="p-3 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                <div className="text-[11px] text-[#59595e] mb-1 font-medium">Emotion</div>
                <EmotionBadge emotion={record.emotion} intensity={record.emotion_intensity} />
              </div>

              <div className="p-3 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                <div className="text-[11px] text-[#59595e] mb-1 font-medium">Status</div>
                <ResolutionBadge status={record.resolution_status} reason={record.resolution_reason} />
              </div>
            </div>

            {/* 5-Point Structured Summary */}
            <div className="p-4 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-2.5">
              <h4 className="text-xs font-bold text-[#1d1d1f] uppercase tracking-wider">
                5-Point Structured Summary
              </h4>
              <div className="space-y-1.5 text-xs">
                <div>
                  <span className="font-semibold text-[#59595e]">Issue: </span>
                  <span className="text-[#1d1d1f] font-medium">{summary?.issue || record.customer_issue}</span>
                </div>
                <div>
                  <span className="font-semibold text-[#59595e]">Customer Request: </span>
                  <span className="text-[#1d1d1f] font-medium">{summary?.customer_request || 'None stated'}</span>
                </div>
                <div>
                  <span className="font-semibold text-[#59595e]">Actions Taken: </span>
                  <span className="text-[#1d1d1f] font-medium">{summary?.actions_taken || 'Categorized and routed'}</span>
                </div>
                <div>
                  <span className="font-semibold text-[#59595e]">Status: </span>
                  <span className="text-[#1d1d1f] font-medium">{summary?.current_status || record.resolution_status}</span>
                </div>
                <div>
                  <span className="font-semibold text-[#59595e]">Priority Assessment: </span>
                  <span className="text-[#1d1d1f] font-medium">{summary?.priority || record.priority} — {record.priority_reason}</span>
                </div>
              </div>
            </div>

            {/* Salient Keywords */}
            {record.keywords && record.keywords.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-[#59595e] uppercase tracking-wider mb-2">
                  Salient Extracted Terms
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {record.keywords.map((kw, i) => (
                    <span key={i} className="px-2.5 py-0.5 rounded-lg bg-black/[0.04] text-[11px] font-mono font-medium text-[#1d1d1f] border border-black/[0.06]">
                      #{kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Interaction Thread Messages */}
            <div className="space-y-2.5">
              <h4 className="text-xs font-bold text-[#1d1d1f] uppercase tracking-wider">
                Interaction Thread ({messages ? messages.length : 1} message{messages && messages.length > 1 ? 's' : ''})
              </h4>
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {messages && messages.length > 0 ? (
                  messages.map((m, idx) => (
                    <div 
                      key={idx} 
                      className={`p-3.5 rounded-2xl border text-xs leading-relaxed ${
                        m.sender === 'agent' || m.sender === 'support'
                          ? 'bg-[#007aff]/10 border-[#007aff]/25 ml-4 text-[#0051a8]'
                          : 'bg-black/[0.03] border-black/[0.06] text-[#1d1d1f]'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px] text-[#59595e] mb-1 font-mono">
                        <span className="font-bold capitalize text-[#1d1d1f]">{m.sender}</span>
                        <span>{m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : ''}</span>
                      </div>
                      <div className="whitespace-pre-wrap font-sans">{m.text}</div>
                    </div>
                  ))
                ) : (
                  <div className="p-3.5 rounded-2xl bg-black/[0.03] border border-black/[0.06] text-xs text-[#1d1d1f] whitespace-pre-wrap font-sans">
                    {record.raw_text_masked}
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>

        {/* PANEL 2: CYBER THREAT INTELLIGENCE DOSSIER */}
        <Card 
          title="Cybersecurity Threat Intelligence" 
          subtitle="Deterministic security rules & behavioral telemetry"
          action={<RiskBadge level={security.risk_level} />}
        >
          <div className="space-y-5">
            {/* Rule Score Gauge */}
            <div className="p-4 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#1d1d1f]">Composite Threat Score</span>
                <span className="font-mono text-base font-bold text-[#1d1d1f] tabular-nums">
                  {security.rule_score} / 100
                </span>
              </div>
              <div className="w-full bg-black/[0.06] rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${
                    security.risk_level === 'Critical'
                      ? 'bg-[#ff3b30]'
                      : security.risk_level === 'High'
                      ? 'bg-[#ff9500]'
                      : security.risk_level === 'Medium'
                      ? 'bg-[#ff9500]'
                      : 'bg-[#34c759]'
                  }`}
                  style={{ width: `${Math.min(security.rule_score, 100)}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-[10px] text-[#59595e] font-mono">
                <span>0 (Routine)</span>
                <span>30 (Medium)</span>
                <span>60 (High)</span>
                <span>80+ (Critical)</span>
              </div>
            </div>

            {/* Attack Techniques Identified */}
            <div>
              <div className="text-[11px] font-bold text-[#59595e] uppercase tracking-wider mb-2">
                Techniques & Threat Type
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="px-2.5 py-1 rounded-lg bg-black/[0.04] text-xs font-semibold text-[#1d1d1f] border border-black/[0.06]">
                  Type: {security.threat_type || 'None'}
                </span>
                {security.techniques && security.techniques.length > 0 ? (
                  security.techniques.map((tech, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-[#ff3b30]/12 text-xs font-bold text-[#b81414] border border-[#ff3b30]/25">
                      {tech}
                    </span>
                  ))
                ) : (
                  <span className="px-2.5 py-1 rounded-lg bg-black/[0.02] text-xs text-[#59595e] border border-black/[0.05]">
                    No malicious social engineering detected
                  </span>
                )}
              </div>
            </div>

            {/* Explainability Risk Reasons */}
            {security.risk_reasons && security.risk_reasons.length > 0 && (
              <div className="p-4 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-2">
                <div className="text-xs font-bold text-[#1d1d1f]">Explainable Decision Reasons</div>
                <ul className="space-y-1.5 text-xs text-[#3c3c43]">
                  {security.risk_reasons.map((r, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-[#b81414] text-sm leading-none">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Findings Breakdown (URLs, Emails, Attachments) */}
            <div className="space-y-3">
              {/* URLs */}
              {security.urls && security.urls.length > 0 && (
                <div className="p-3.5 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-1.5 text-xs">
                  <div className="font-bold text-[#1d1d1f] flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-[#007aff]" />
                    Detected URLs ({security.urls.length})
                  </div>
                  {security.urls.map((u, i) => (
                    <div key={i} className="font-mono text-[11px] text-[#59595e] break-all pl-5">
                      • {u.url} {u.lookalike_of && <span className="text-[#b81414] font-bold">[Lookalike of {u.lookalike_of}]</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Emails */}
              {security.emails && security.emails.length > 0 && (
                <div className="p-3.5 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-1.5 text-xs">
                  <div className="font-bold text-[#1d1d1f] flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-[#007aff]" />
                    Analyzed Email Addresses ({security.emails.length})
                  </div>
                  {security.emails.map((e, i) => (
                    <div key={i} className="font-mono text-[11px] text-[#59595e] break-all pl-5">
                      • {e.address} {e.free_mail && <span className="text-[#a53c00] font-semibold">[Free-mail domain]</span>} {e.domain_mismatch && <span className="text-[#b81414] font-bold">[Display name brand mismatch]</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Attachments */}
              {security.attachments && security.attachments.length > 0 && (
                <div className="p-3.5 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-1.5 text-xs">
                  <div className="font-bold text-[#1d1d1f] flex items-center gap-1.5">
                    <Paperclip className="w-3.5 h-3.5 text-[#007aff]" />
                    Analyzed Attachments ({security.attachments.length})
                  </div>
                  {security.attachments.map((a, i) => (
                    <div key={i} className="font-mono text-[11px] text-[#59595e] break-all pl-5">
                      • {a.filename} {a.risk === 'High' && <span className="text-[#b81414] font-bold">[Dangerous / Executable]</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </Card>

      </div>

      {/* ADMIN-ONLY PRIVATE INTERNAL NOTES (Section 14 & 15) */}
      {adminMode && (
        <Card 
          title="Internal Administrative Notes" 
          subtitle="Privileged operator notes — strictly invisible to customer endpoints"
          icon={Lock}
        >
          <div className="space-y-4">
            <div className="space-y-2.5 max-h-60 overflow-y-auto">
              {record.internal_notes && record.internal_notes.length > 0 ? (
                record.internal_notes.map((note) => (
                  <div key={note.id} className="p-3 bg-neutral-50 rounded-xl border border-neutral-200/80 text-xs">
                    <div className="flex items-center justify-between text-[11px] text-neutral-500 mb-1 font-mono">
                      <span className="font-bold text-neutral-800">{note.author_name || 'Administrator'}</span>
                      <span>{new Date(note.created_at).toLocaleString()}</span>
                    </div>
                    <div className="text-neutral-700 whitespace-pre-wrap">{note.text}</div>
                  </div>
                ))
              ) : (
                <div className="p-4 rounded-xl bg-neutral-50 border border-neutral-200/60 text-center text-xs text-neutral-400">
                  No internal notes recorded yet. Add notes to coordinate resolution among operators.
                </div>
              )}
            </div>

            <form onSubmit={handleAddNote} className="flex gap-2">
              <input
                type="text"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add confidential operator note (audit logged)..."
                className="flex-1 px-3 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl outline-none focus:bg-white focus:border-neutral-900 transition"
              />
              <button
                type="submit"
                disabled={submittingNote || !noteText.trim()}
                className="px-4 py-2 bg-neutral-900 text-white rounded-xl text-xs font-semibold hover:bg-neutral-800 disabled:opacity-50 transition flex items-center gap-1.5"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Save Note</span>
              </button>
            </form>
          </div>
        </Card>
      )}

      {/* Raw Section 5 JSON Drawer */}
      <Card 
        title="Section 5 Locked JSON Contract" 
        subtitle="Verifiable canonical schema output for enterprise compliance"
        icon={FileText}
      >
        <div className="relative">
          <pre className="p-4 rounded-xl bg-[#f5f5f7] border border-black/[0.08] text-[#1d1d1f] font-mono text-xs overflow-x-auto max-h-72 leading-relaxed">
            {JSON.stringify(record, null, 2)}
          </pre>
        </div>
      </Card>

      {/* MODAL: ADMIN REVIEW & CALIBRATION (Section 13) */}
      {showReviewModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-neutral-200 shadow-2xl max-w-lg w-full p-6 space-y-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-neutral-900">Review & Calibrate Classification</h3>
                <p className="text-xs text-neutral-500">Correct AI classification; baseline AI values are preserved in history.</p>
              </div>
              <button onClick={() => setShowReviewModal(false)} className="p-1 rounded-lg hover:bg-neutral-100 text-neutral-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-[11px] font-semibold text-neutral-700 mb-1">Canonical Category</label>
                <select
                  value={reviewCat}
                  onChange={(e) => setReviewCat(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
                >
                  {CANONICAL_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-neutral-700 mb-1">Controlled Issue Label</label>
                <select
                  value={reviewLabel}
                  onChange={(e) => setReviewLabel(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
                >
                  {CANONICAL_ISSUE_LABELS.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-neutral-700 mb-1">Priority</label>
                  <select
                    value={reviewPrio}
                    onChange={(e) => setReviewPrio(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-neutral-700 mb-1">Security Risk Level</label>
                  <select
                    value={reviewRisk}
                    onChange={(e) => setReviewRisk(e.target.value)}
                    className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Critical">Critical</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-neutral-700 mb-1">Resolution Status</label>
                <select
                  value={reviewStatus}
                  onChange={(e) => setReviewStatus(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
                >
                  <option value="Pending">Pending</option>
                  <option value="Unresolved">Unresolved</option>
                  <option value="Resolved">Resolved</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-neutral-700 mb-1">Calibration Justification</label>
                <textarea
                  rows={2}
                  value={reviewReason}
                  onChange={(e) => setReviewReason(e.target.value)}
                  placeholder="Explain reason for manual adjustment (recorded in audit registry)..."
                  className="w-full px-3 py-2 bg-neutral-50 border border-neutral-200 rounded-xl outline-none focus:bg-white transition"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-neutral-100">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="px-3.5 py-2 rounded-xl border border-neutral-200 text-neutral-700 hover:bg-neutral-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="px-4 py-2 bg-neutral-900 text-white rounded-xl font-semibold hover:bg-neutral-800 transition"
                >
                  {submittingReview ? 'Submitting...' : 'Save Calibration'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: AI DRAFT RESPONSE */}
      {showDraftModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-neutral-200 shadow-2xl max-w-xl w-full p-6 space-y-4 animate-scale-in">
            <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <h3 className="text-base font-bold text-neutral-900">AI Customer Reply Assistant</h3>
              </div>
              <button onClick={() => setShowDraftModal(false)} className="p-1 rounded-lg hover:bg-neutral-100 text-neutral-400">
                <X className="w-4 h-4" />
              </button>
            </div>

            {loadingDraft ? (
              <div className="p-8 text-center text-xs text-neutral-400">Synthesizing recommended response...</div>
            ) : draftData ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-200/80">
                  <div className="text-[10px] uppercase font-bold text-neutral-500 mb-1">Recommended Operational Action</div>
                  <div className="text-neutral-900 font-medium">{draftData.recommended_action}</div>
                </div>

                <div>
                  <div className="text-[10px] uppercase font-bold text-neutral-500 mb-1">Advisory Response Draft</div>
                  <textarea
                    rows={6}
                    readOnly
                    value={draftData.draft_response}
                    className="w-full p-3 bg-neutral-50 border border-neutral-200 rounded-xl font-sans text-xs outline-none"
                  />
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-neutral-100">
                  <span className="text-[11px] text-neutral-400">Advisory suggestion. Review before sending to customer.</span>
                  <button
                    onClick={handleCopyDraft}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-neutral-900 text-white rounded-xl font-semibold hover:bg-neutral-800 transition"
                  >
                    {copiedDraft ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedDraft ? 'Copied' : 'Copy to Clipboard'}</span>
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

    </div>
  );
}
