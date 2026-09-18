"""
F5, E2, E5, E8. Analytics Aggregations, Frequently Reported Issues, Trends & Evaluation.
Calculates dashboard KPI metrics, ranked issue frequencies, temporal trends, and system accuracy benchmarks.
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

from app.schemas import (
    DashboardResponse,
    DashboardKPIs,
    IssueFrequencyResponse,
    RankedIssue,
    EvaluationMetrics,
    ConversationRecord,
)
from app.db import get_all_conversations
from app.pipeline import process_conversation

EVAL_DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "labeled_eval.json")


def compute_dashboard_data() -> DashboardResponse:
    """
    Computes real-time KPI metrics, distributions, and trends across all conversations.
    """
    conversations = get_all_conversations()
    total = len(conversations)

    if total == 0:
        return DashboardResponse(
            kpis=DashboardKPIs(),
            sentiment_distribution={"Positive": 0, "Neutral": 0, "Negative": 0},
            category_distribution={},
            issue_frequency=[],
            risk_distribution={"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
            emotion_distribution={},
            daily_trend=[],
        )

    # 1. KPI Counts
    pos_count = sum(1 for c in conversations if c.sentiment == "Positive")
    neu_count = sum(1 for c in conversations if c.sentiment == "Neutral")
    neg_count = sum(1 for c in conversations if c.sentiment == "Negative")
    unresolved_count = sum(1 for c in conversations if c.resolution_status == "Unresolved")
    critical_count = sum(
        1 for c in conversations if c.priority == "Critical" or c.security.risk_level == "Critical"
    )
    threats_detected = sum(1 for c in conversations if c.security.threat_detected)
    angry_customers = sum(1 for c in conversations if c.is_angry)

    # 2. Distributions
    categories = Counter(c.category for c in conversations)
    issues = Counter(c.issue_label for c in conversations)
    risks = Counter(c.security.risk_level for c in conversations)
    emotions = Counter(c.emotion for c in conversations)

    most_common_cat = categories.most_common(1)[0][0] if categories else "None"
    most_common_issue = issues.most_common(1)[0][0] if issues else "None"

    # Total complaints (negative sentiment or non-Other issues)
    total_complaints = sum(1 for c in conversations if c.sentiment == "Negative" or c.category != "Other")

    kpis = DashboardKPIs(
        total_conversations=total,
        total_complaints=total_complaints,
        positive_count=pos_count,
        neutral_count=neu_count,
        negative_count=neg_count,
        most_common_complaint=most_common_cat,
        most_frequent_issue=most_common_issue,
        unresolved_count=unresolved_count,
        critical_count=critical_count,
        threats_detected=threats_detected,
        angry_customers=angry_customers,
    )

    # 3. Ranked Issue Frequencies (F5)
    ranked_issues: List[RankedIssue] = []
    for issue, count in issues.most_common(10):
        pct = round((count / total) * 100, 1)
        ranked_issues.append(
            RankedIssue(
                issue_label=issue,
                count=count,
                percentage=pct,
                trend="neutral",
            )
        )

    # 4. Daily Trend
    trend_map: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "complaints": 0, "threats": 0})
    for c in conversations:
        # Extract YYYY-MM-DD
        date_str = c.created_at[:10] if len(c.created_at) >= 10 else "Today"
        trend_map[date_str]["total"] += 1
        if c.sentiment == "Negative":
            trend_map[date_str]["complaints"] += 1
        if c.security.threat_detected:
            trend_map[date_str]["threats"] += 1

    sorted_dates = sorted(trend_map.keys())
    daily_trend = [
        {"date": d, "total": trend_map[d]["total"], "complaints": trend_map[d]["complaints"], "threats": trend_map[d]["threats"]}
        for d in sorted_dates
    ]

    return DashboardResponse(
        kpis=kpis,
        sentiment_distribution={
            "Positive": pos_count,
            "Neutral": neu_count,
            "Negative": neg_count,
        },
        category_distribution=dict(categories.most_common(10)),
        issue_frequency=ranked_issues,
        risk_distribution={
            "Low": risks.get("Low", 0),
            "Medium": risks.get("Medium", 0),
            "High": risks.get("High", 0),
            "Critical": risks.get("Critical", 0),
        },
        emotion_distribution=dict(emotions.most_common(8)),
        daily_trend=daily_trend,
    )


def compute_ranked_issues(days: Optional[int] = None) -> IssueFrequencyResponse:
    """
    F5: Returns ranked table of canonical issue labels by frequency.
    """
    conversations = get_all_conversations()
    if days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        conversations = [c for c in conversations if c.created_at >= cutoff]

    total = len(conversations)
    if total == 0:
        return IssueFrequencyResponse(total_conversations=0, issues=[])

    issues = Counter(c.issue_label for c in conversations)
    ranked = []
    for label, count in issues.most_common():
        pct = round((count / total) * 100, 1)
        ranked.append(RankedIssue(issue_label=label, count=count, percentage=pct))

    return IssueFrequencyResponse(total_conversations=total, issues=ranked)


def compute_trends(bucket: str = "day") -> List[Dict[str, Any]]:
    """
    E5: Aggregates conversations into temporal buckets (day, week, month).
    """
    conversations = get_all_conversations()
    groups: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "complaints": 0, "threats": 0, "unresolved": 0})

    for c in conversations:
        dt_str = c.created_at
        if bucket == "month" and len(dt_str) >= 7:
            key = dt_str[:7]
        elif bucket == "week" and len(dt_str) >= 10:
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
            except Exception:
                key = dt_str[:10]
        else:
            key = dt_str[:10] if len(dt_str) >= 10 else "Unknown"

        groups[key]["total"] += 1
        if c.sentiment == "Negative":
            groups[key]["complaints"] += 1
        if c.security.threat_detected:
            groups[key]["threats"] += 1
        if c.resolution_status == "Unresolved":
            groups[key]["unresolved"] += 1

    sorted_keys = sorted(groups.keys())
    return [
        {
            "period": k,
            "total": groups[k]["total"],
            "complaints": groups[k]["complaints"],
            "threats": groups[k]["threats"],
            "unresolved": groups[k]["unresolved"],
        }
        for k in sorted_keys
    ]


def run_system_evaluation() -> EvaluationMetrics:
    """
    E8: Evaluates system precision, recall, and false positive rate
    on the ground-truth benchmark test set (data/labeled_eval.json).
    """
    if not os.path.exists(EVAL_DATASET_PATH):
        return EvaluationMetrics(
            total_eval_samples=0,
            recall=1.0,
            precision=1.0,
            f1_score=1.0,
            false_positive_rate=0.0,
            avg_latency_ms=0.0,
            ai_mode="fallback",
        )

    with open(EVAL_DATASET_PATH, "r") as f:
        eval_samples = json.load(f)

    tp = 0
    fp = 0
    tn = 0
    fn = 0
    latencies: List[float] = []

    ai_mode_used = "fallback"

    for sample in eval_samples:
        conv_dict = {
            "conversation_id": sample.get("id"),
            "channel": sample.get("channel", "chat"),
            "text": sample.get("text", ""),
            "attachments": sample.get("attachments", []),
            "source": "synthetic",
        }

        t0 = time.time()
        record = process_conversation(conv_dict, persist=False)
        t1 = time.time()
        latencies.append((t1 - t0) * 1000)

        ai_mode_used = record.ai_mode
        expected_threat = bool(sample.get("expected_threat", False))
        predicted_threat = bool(record.security.threat_detected)

        if predicted_threat and expected_threat:
            tp += 1
        elif predicted_threat and not expected_threat:
            fp += 1
        elif not predicted_threat and not expected_threat:
            tn += 1
        else:
            fn += 1

    total_samples = len(eval_samples)
    recall = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 100.0
    precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 100.0
    fpr = round((fp / (fp + tn)) * 100, 2) if (fp + tn) > 0 else 0.0
    f1 = round((2 * precision * recall) / (precision + recall), 2) if (precision + recall) > 0 else 100.0
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0

    return EvaluationMetrics(
        total_eval_samples=total_samples,
        recall=recall,
        precision=precision,
        f1_score=f1,
        false_positive_rate=fpr,
        avg_latency_ms=avg_latency,
        ai_mode=ai_mode_used,
    )
