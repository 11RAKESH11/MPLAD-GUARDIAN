"""
MPLAD GUARDIAN — Multi-Signal Candidate-Blocked Duplicate Detection Engine (Phase 5)

Multi-Signal Weighting (Phase 5.5):
  - Text Similarity (Word TF-IDF): 35%
  - Semantic / N-gram Similarity (Char N-gram TF-IDF): 25%
  - Location Proximity (Constituency / District / State): 25%
  - Financial Amount Parity: 15%

Candidate Blocking (Phase 5.7 & 5.36):
  - Partitions candidate search by (District + Category) to avoid O(N²) all-pairs explosion.
  - Scales linearly across 96,654 projects.
"""

from typing import Dict, Any, List, Tuple
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DuplicateEngine:
    def __init__(
        self,
        weight_text: float = 0.35,
        weight_semantic: float = 0.25,
        weight_location: float = 0.25,
        weight_amount: float = 0.15,
        min_threshold: float = 65.0
    ):
        self.w_text = weight_text
        self.w_semantic = weight_semantic
        self.w_loc = weight_location
        self.w_amt = weight_amount
        self.threshold = min_threshold
        
    def find_duplicates_for_blocks(self, projects: List[Dict[str, Any]], max_per_block: int = 50) -> Dict[str, Dict[str, Any]]:
        """
        Runs candidate-blocked duplicate detection across all projects.
        Returns map of work_code -> { score, matched_pairs: [...] }
        """
        blocks = defaultdict(list)
        for p in projects:
            code = p.get("work_code")
            dist = str(p.get("district") or "Unknown")
            cat = str(p.get("category") or "Normal/Others")
            desc = str(p.get("description") or p.get("work_type") or "").strip()
            amt = float(p.get("sanctioned_amount") or p.get("recommended_amount") or 0.0)
            const = str(p.get("constituency") or "").strip()
            
            if len(desc) >= 12 and code:
                blocks[f"{dist}:{cat}"].append({
                    "work_code": code,
                    "text": desc,
                    "amount": amt,
                    "district": dist,
                    "constituency": const,
                    "state": str(p.get("state") or "")
                })
                
        results = defaultdict(lambda: {"score": 0.0, "matched_pairs": []})
        
        for block_key, items in blocks.items():
            if len(items) < 2:
                continue
                
            selected = items[:max_per_block]
            texts = [it["text"] for it in selected]
            
            try:
                # Word-level TF-IDF
                word_vec = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', min_df=1)
                w_mat = word_vec.fit_transform(texts)
                w_sim = cosine_similarity(w_mat)
                
                # Character n-gram TF-IDF (captures spelling variations / typo resilience)
                char_vec = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 4), min_df=1)
                c_mat = char_vec.fit_transform(texts)
                c_sim = cosine_similarity(c_mat)
                
                n = len(selected)
                for i in range(n):
                    it_i = selected[i]
                    code_i = it_i["work_code"]
                    amt_i = it_i["amount"]
                    const_i = it_i["constituency"]
                    
                    for j in range(i + 1, n):
                        it_j = selected[j]
                        code_j = it_j["work_code"]
                        amt_j = it_j["amount"]
                        const_j = it_j["constituency"]
                        
                        s_text = float(w_sim[i, j])
                        s_char = float(c_sim[i, j])
                        
                        # Only proceed if there is non-trivial text similarity
                        if s_text < 0.60 and s_char < 0.65:
                            continue
                            
                        # Location similarity
                        if const_i and const_j and const_i.lower() == const_j.lower():
                            s_loc = 1.0
                        elif it_i["district"].lower() == it_j["district"].lower():
                            s_loc = 0.85
                        else:
                            s_loc = 0.50
                            
                        # Amount similarity
                        if amt_i > 0 and amt_j > 0:
                            diff_ratio = abs(amt_i - amt_j) / max(amt_i, amt_j)
                            s_amt = max(0.0, 1.0 - diff_ratio)
                        else:
                            s_amt = 0.50
                            
                        # Multi-signal composite score (0–100)
                        raw_sim = (
                            (self.w_text * s_text) +
                            (self.w_semantic * s_char) +
                            (self.w_loc * s_loc) +
                            (self.w_amt * s_amt)
                        ) * 100.0
                        
                        composite_score = round(raw_sim, 1)
                        
                        if composite_score >= self.threshold:
                            evidence = {
                                "text_similarity_pct": round(s_text * 100, 1),
                                "semantic_ngram_pct": round(s_char * 100, 1),
                                "location_similarity_pct": round(s_loc * 100, 1),
                                "amount_similarity_pct": round(s_amt * 100, 1),
                                "target_amount": amt_i,
                                "matched_amount": amt_j,
                                "locality": it_i["district"]
                            }
                            
                            reason = (
                                f"High multi-signal similarity ({composite_score:.0f}%) with {code_j} "
                                f"(Text: {s_text*100:.0f}%, Amount Parity: {s_amt*100:.0f}% in {it_i['district']})."
                            )
                            
                            results[code_i]["score"] = max(results[code_i]["score"], composite_score)
                            results[code_i]["matched_pairs"].append({
                                "matched_work_code": code_j,
                                "similarity_score": composite_score,
                                "reason": reason,
                                "evidence": evidence
                            })
                            
                            results[code_j]["score"] = max(results[code_j]["score"], composite_score)
                            results[code_j]["matched_pairs"].append({
                                "matched_work_code": code_i,
                                "similarity_score": composite_score,
                                "reason": reason,
                                "evidence": evidence
                            })
            except Exception:
                continue
                
        return results

    def evaluate_single_project(self, project: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluates duplicate risk for a single project against a list of candidate peer projects."""
        code = project.get("work_code", "TARGET")
        desc = str(project.get("description") or project.get("work_type") or "").strip()
        amt = float(project.get("sanctioned_amount") or 0.0)
        dist = str(project.get("district") or "")
        const = str(project.get("constituency") or "")
        
        if len(desc) < 10 or not candidates:
            return {
                "score": 0.0,
                "severity": "LOW",
                "matched_count": 0,
                "top_matches": [],
                "explanation": "No candidate project records available in locality for duplicate analysis."
            }
            
        all_texts = [desc] + [str(c.get("description") or c.get("work_type") or "") for c in candidates]
        try:
            vec = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', min_df=1)
            mat = vec.fit_transform(all_texts)
            sims = cosine_similarity(mat[0:1], mat[1:])[0]
            
            matches = []
            for idx, c in enumerate(candidates):
                t_sim = float(sims[idx])
                if t_sim >= 0.60:
                    c_amt = float(c.get("sanctioned_amount") or 0.0)
                    c_const = str(c.get("constituency") or "")
                    s_loc = 1.0 if const and c_const and const.lower() == c_const.lower() else 0.85
                    s_amt = max(0.0, 1.0 - (abs(amt - c_amt) / max(amt, c_amt, 1.0)))
                    
                    comp = round((0.40 * t_sim + 0.25 * t_sim + 0.20 * s_loc + 0.15 * s_amt) * 100, 1)
                    if comp >= self.threshold:
                        matches.append({
                            "work_code": c.get("work_code"),
                            "similarity": comp,
                            "text_sim": round(t_sim * 100, 1),
                            "work_type": c.get("work_type"),
                            "amount": c_amt
                        })
                        
            matches.sort(key=lambda x: x["similarity"], reverse=True)
            top_score = matches[0]["similarity"] if matches else 0.0
            
            return {
                "score": top_score,
                "severity": "HIGH" if top_score >= 75 else ("MEDIUM" if top_score >= 50 else "LOW"),
                "matched_count": len(matches),
                "top_matches": matches[:5],
                "explanation": (
                    f"Found {len(matches)} potential duplicate submission(s) with up to {top_score:.0f}% multi-signal similarity in {dist}."
                    if matches else "No duplicate works detected across peer projects in the same district."
                )
            }
        except Exception:
            return {
                "score": 0.0,
                "severity": "LOW",
                "matched_count": 0,
                "top_matches": [],
                "explanation": "Text vectorization error during similarity analysis."
            }
