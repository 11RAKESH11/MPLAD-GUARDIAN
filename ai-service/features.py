"""
MPLAD GUARDIAN — Feature Engineering Pipeline (Phase 5)

Extracts standardized, normalized feature vectors for project risk evaluation:
- Financial features (utilization ratio, expenditure ratio, scale index)
- Temporal features (age in months, delay metrics)
- Text tokenization & representation
- Evidence availability and missing data tracking
"""

from typing import Dict, Any, List, Optional
import datetime
import math
import re

def parse_date_str(date_val: Optional[str]) -> Optional[datetime.date]:
    """Parse various date formats into standard datetime.date."""
    if not date_val or date_val in ("NA", "N/A", "None", "null", "", "-"):
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(date_val[:10], fmt).date()
        except Exception:
            continue
    return None

def extract_project_features(project: Dict[str, Any], reference_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Extracts structured feature vector and evidence availability matrix for a single project.
    Missing data remains explicitly tracked as missing.
    """
    ref_date = reference_date or datetime.date(2026, 8, 28)
    
    # Financial features
    sanctioned = float(project.get("sanctioned_amount") or 0.0)
    recommended = float(project.get("recommended_amount") or 0.0)
    disbursed = float(project.get("disbursed_amount") or 0.0)
    expenditure = float(project.get("expenditure_amount") or 0.0)
    
    has_sanctioned = sanctioned > 0
    has_recommended = recommended > 0
    has_expenditure = expenditure > 0 or disbursed > 0
    
    effective_base = sanctioned if has_sanctioned else recommended
    effective_spent = max(disbursed, expenditure)
    
    utilization_ratio = (effective_spent / effective_base) if effective_base > 0 else 0.0
    sanction_to_recommend_ratio = (sanctioned / recommended) if (has_sanctioned and has_recommended) else 1.0
    financial_materiality_log = math.log10(max(1.0, sanctioned)) if has_sanctioned else 0.0
    
    # Temporal features
    sanction_date = parse_date_str(project.get("sanction_date"))
    recommended_date = parse_date_str(project.get("recommended_date"))
    completion_date = parse_date_str(project.get("completion_date"))
    
    has_sanction_date = sanction_date is not None
    has_completion_date = completion_date is not None
    
    age_months = 0.0
    if has_sanction_date:
        age_days = (ref_date - sanction_date).days
        age_months = max(0.0, age_days / 30.44)
    elif project.get("financial_year"):
        # Infer approximate age from FY (e.g., '2023-2024' -> ~30 months from start)
        m = re.match(r"^(\d{4})", str(project.get("financial_year")))
        if m:
            start_year = int(m.group(1))
            age_months = max(0.0, (ref_date.year - start_year) * 12.0)
            
    # Text features
    description = str(project.get("description") or "").strip()
    work_type = str(project.get("work_type") or "").strip()
    combined_text = f"{work_type} {description}".strip()
    text_length = len(combined_text)
    has_rich_text = text_length >= 25
    
    # Geographic features
    state = str(project.get("state") or "").strip()
    district = str(project.get("district") or "").strip()
    constituency = str(project.get("constituency") or "").strip()
    has_district = len(district) > 0
    has_state = len(state) > 0
    has_gps = bool(project.get("latitude") and project.get("longitude"))
    
    # Calculate evidence coverage score (0–100%)
    evidence_points = 0
    max_points = 7
    if has_sanctioned: evidence_points += 1
    if has_expenditure: evidence_points += 1
    if has_sanction_date or age_months > 0: evidence_points += 1
    if has_state and has_district: evidence_points += 1
    if has_rich_text: evidence_points += 1
    if project.get("category"): evidence_points += 1
    if project.get("mp_name"): evidence_points += 1
    
    evidence_coverage_pct = round((evidence_points / max_points) * 100.0, 1)
    
    return {
        "work_code": project.get("work_code"),
        "category": project.get("category") or "Normal/Others",
        "state": state,
        "district": district,
        "constituency": constituency,
        "status": project.get("status") or "Proposed",
        "financial_year": project.get("financial_year") or "Unknown",
        "sanctioned_amount": sanctioned,
        "recommended_amount": recommended,
        "expenditure_amount": expenditure,
        "disbursed_amount": disbursed,
        "effective_base_amount": effective_base,
        "effective_spent_amount": effective_spent,
        "utilization_ratio": utilization_ratio,
        "utilization_pct": round(utilization_ratio * 100.0, 2),
        "sanction_to_recommend_ratio": sanction_to_recommend_ratio,
        "financial_materiality_log": financial_materiality_log,
        "sanction_date": sanction_date.isoformat() if sanction_date else None,
        "completion_date": completion_date.isoformat() if completion_date else None,
        "age_months": round(age_months, 1),
        "combined_text": combined_text,
        "text_length": text_length,
        "has_rich_text": has_rich_text,
        "has_gps": has_gps,
        "has_district": has_district,
        "has_sanctioned": has_sanctioned,
        "has_sanction_date": has_sanction_date,
        "has_completion_date": has_completion_date,
        "evidence_coverage_pct": evidence_coverage_pct,
        "evidence_available_dimensions": {
            "financial": has_sanctioned,
            "temporal": has_sanction_date or age_months > 0,
            "text": has_rich_text,
            "geographic": has_district,
            "lifecycle": project.get("status") is not None
        }
    }
