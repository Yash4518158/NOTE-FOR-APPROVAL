import logging
from authentication.models import NFARequest, NFAApprovalHistory
from authentication.ai.services.policy_retriever import PolicyRetriever
from authentication.ai.services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class ApprovalPredictor:
    """Historical & Rule-Based Approval Probability Prediction Engine"""

    _dept_ratio_cache = {}

    @classmethod
    def predict_approval_probability(cls, nfa: NFARequest, attachment_count: int = None, skip_rag: bool = False) -> dict:
        try:
            total_amount = float(nfa.total_amount or 0)
            justification = nfa.business_justification or ''
            commercial = nfa.commercial_impact or ''
            if attachment_count is None:
                attachment_count = nfa.attachments.filter(is_deleted=False).count()
            dept_name = nfa.department.department_name if nfa.department else 'General'

            # 1. RAG Policy & Quality Audit Score (0 - 100)
            policies = []
            if skip_rag:
                rag_score = 75.0
            else:
                nfa_payload = {
                    'title': nfa.title,
                    'department_name': dept_name,
                    'total_amount_inr': total_amount,
                    'business_justification': justification,
                    'commercial_impact': commercial,
                    'vendor_name': nfa.vendor_name or '',
                    'attachment_count': attachment_count
                }
                policies = PolicyRetriever.retrieve_relevant_policies(nfa_payload)
                rag_review = LLMProvider._heuristic_rag_review(nfa_payload, policies)
                rag_score = float(rag_review.get('readiness_score', 80))

            # 2. Quotation & Attachment Completeness Score (0 - 100)
            doc_score = 100.0
            positive_factors = []
            risk_factors = []

            if total_amount >= 50000:
                if attachment_count >= 3:
                    positive_factors.append(f"Contains {attachment_count} attachments matching competitive bidding policy.")
                elif attachment_count >= 1:
                    doc_score -= 30.0
                    risk_factors.append(f"Only {attachment_count} attachment attached for request > ₹50,000 (3 recommended).")
                else:
                    doc_score -= 60.0
                    risk_factors.append("No supplier quotes attached for purchase > ₹50,000.")
            else:
                if attachment_count >= 1:
                    positive_factors.append(f"{attachment_count} attachment supporting request attached.")

            # 3. Department Historical Approval Ratio (0 - 100) - Cached in memory
            dept_id = nfa.department_id if nfa.department else 0
            if dept_id in cls._dept_ratio_cache:
                dept_score = cls._dept_ratio_cache[dept_id]
                positive_factors.append(f"Department '{dept_name}' has a {int(dept_score)}% historical approval rate.")
            else:
                dept_score = 85.0
                try:
                    dept_nfas = NFARequest.objects.filter(department=nfa.department).exclude(current_status='DRAFT')
                    total_dept_count = dept_nfas.count()
                    if total_dept_count >= 3:
                        approved_count = dept_nfas.filter(current_status='APPROVED').count()
                        dept_score = (approved_count / total_dept_count) * 100.0
                    cls._dept_ratio_cache[dept_id] = dept_score
                    positive_factors.append(f"Department '{dept_name}' has a {int(dept_score)}% historical approval rate.")
                except Exception as e:
                    logger.debug(f"[ApprovalPredictor] Dept history error: {str(e)}")


            # 4. Text Quality & Clarity Score (0 - 100)
            quality_score = 100.0
            if len(justification) > 30 and len(commercial) > 20:
                positive_factors.append("Strong business justification and commercial ROI details provided.")
            elif len(justification) < 20:
                quality_score -= 40.0
                risk_factors.append("Business justification is brief and lacks detail.")

            if total_amount >= 500000:
                risk_factors.append("High amount request (≥ ₹500,000) requiring mandatory Level 3 CFO approval.")

            # 5. Weighted Formula Calculation
            # Final Probability = (0.35 * RAG) + (0.25 * Doc) + (0.20 * Dept) + (0.20 * Quality)
            probability = (0.35 * rag_score) + (0.25 * doc_score) + (0.20 * dept_score) + (0.20 * quality_score)
            probability = max(5, min(99, int(round(probability))))

            # Determine Tier & Color Badges
            if probability >= 75:
                tier = "HIGH"
                risk_level = "LOW"
                badge_bg = "#dcfce7"
                badge_text = "#15803d"
            elif probability >= 50:
                tier = "MODERATE"
                risk_level = "MEDIUM"
                badge_bg = "#fef3c7"
                badge_text = "#b45309"
            else:
                tier = "LOW"
                risk_level = "HIGH"
                badge_bg = "#fee2e2"
                badge_text = "#b91c1c"

            if not positive_factors:
                positive_factors.append("Standard procurement request structure.")

            return {
                "approval_probability_percentage": probability,
                "likelihood_tier": tier,
                "risk_level": risk_level,
                "badge_bg_color": badge_bg,
                "badge_text_color": badge_text,
                "positive_factors": positive_factors,
                "risk_factors": risk_factors,
                "rag_readiness_score": rag_score,
                "matched_policy_count": len(policies)
            }

        except Exception as e:
            logger.error(f"[ApprovalPredictor] Prediction calculation error: {str(e)}")
            return {
                "approval_probability_percentage": 75,
                "likelihood_tier": "MODERATE",
                "risk_level": "LOW",
                "badge_bg_color": "#eff6ff",
                "badge_text_color": "#2563eb",
                "positive_factors": ["Standard NFA submission"],
                "risk_factors": [],
                "rag_readiness_score": 75,
                "matched_policy_count": 0
            }
