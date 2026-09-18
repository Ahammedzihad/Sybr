"""
E1. Dangerous Attachment Analysis Engine.
Flags high-risk file types, script formats, macro-enabled documents, and deceptive double extensions.
"""
import os
import re
from typing import List
from app.schemas import AttachmentFinding

# Direct execution formats
EXECUTABLE_EXTENSIONS = {
    "exe", "scr", "bat", "js", "vbs", "msi", "apk", "cmd", "ps1", "pif", "hta", "wsf", "cpl", "jar"
}

# Macro-enabled office documents
MACRO_EXTENSIONS = {
    "docm", "xlsm", "pptm", "dotm", "xltm"
}

# Disk image / container extensions frequently used to bypass email filters
CONTAINER_EXTENSIONS = {
    "iso", "img", "vhd", "vhdx"
}

SAFE_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "txt", "csv", "xlsx", "docx", "pptx"
}


def analyze_attachment(filename: str) -> AttachmentFinding:
    """
    Analyzes an attachment filename for malicious extension techniques and risk cues.
    """
    clean_name = os.path.basename(filename.strip().strip("'\""))
    parts = clean_name.lower().split(".")

    if len(parts) > 1:
        extension = parts[-1]
    else:
        extension = ""

    score = 0
    reasons: List[str] = []

    # 1. Double extension check (+35) (e.g. invoice.pdf.exe)
    if len(parts) > 2:
        penultimate_ext = parts[-2]
        if penultimate_ext in SAFE_EXTENSIONS or penultimate_ext in {"doc", "xls", "ppt", "zip"}:
            if extension in EXECUTABLE_EXTENSIONS or extension in MACRO_EXTENSIONS:
                score += 35
                reasons.append(
                    f"Deceptive double extension detected (masquerades as '.{penultimate_ext}', actually executable '.{extension}') (+35)"
                )

    # 2. Direct executable extension (+40)
    if extension in EXECUTABLE_EXTENSIONS:
        score += 40
        reasons.append(f"Dangerous executable/script file type '.{extension}' (+40)")

    # 3. Macro-enabled document (+30)
    elif extension in MACRO_EXTENSIONS:
        score += 30
        reasons.append(f"Macro-enabled Office document '.{extension}' capable of payload execution (+30)")

    # 4. Container / disk image format (+20)
    elif extension in CONTAINER_EXTENSIONS:
        score += 20
        reasons.append(f"Disk container format '.{extension}' frequently used to deliver malware (+20)")

    # 5. Archive with password indication (+20)
    if "password" in clean_name.lower() or "pwd" in clean_name.lower():
        score += 20
        reasons.append("Filename references password protection (often used to evade anti-malware scanners) (+20)")

    # Determine risk band
    if score >= 50:
        risk = "High"
    elif score >= 25:
        risk = "Medium"
    else:
        risk = "Low"

    return AttachmentFinding(
        filename=clean_name,
        extension=extension,
        risk=risk,
        reasons=reasons,
    )
