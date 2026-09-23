from authentication.models import NFARequest
from authentication.ai.services.llm_provider import LLMProvider
from authentication.ai.services.policy_retriever import PolicyRetriever
from authentication.ai.services.approval_predictor import ApprovalPredictor

class NFAReviewService:
    """Phase 2 RAG Enabled NFA Review & Approval Probability Service"""

    @staticmethod
    def prepare_ai_input(nfa: NFARequest) -> dict:
        return {
            'nfa_number': nfa.nfa_number,
            'title': nfa.title,
            'department_name': nfa.department.department_name if nfa.department else 'N/A',
            'project_name': nfa.project_name or 'General',
            'vendor_name': nfa.vendor_name or 'N/A',
            'total_amount_inr': float(nfa.total_amount or 0),
            'business_justification': nfa.business_justification or '',
            'commercial_impact': nfa.commercial_impact or '',
            'current_status': nfa.current_status,
            'attachment_count': nfa.attachments.filter(is_deleted=False).count(),
            'buyer_name': nfa.buyer.employee.full_name if (nfa.buyer and hasattr(nfa.buyer, 'employee') and nfa.buyer.employee) else (nfa.buyer.username if nfa.buyer else 'Buyer')
        }

    @staticmethod
    def review_nfa(nfa: NFARequest) -> dict:
        ai_input = NFAReviewService.prepare_ai_input(nfa)
        policies = PolicyRetriever.retrieve_relevant_policies(ai_input)
        review = LLMProvider.generate_review(ai_input, policies)
        prediction = ApprovalPredictor.predict_approval_probability(nfa)
        review['approval_prediction'] = prediction
        return review

    @staticmethod
    def review_draft_payload(draft_payload: dict) -> dict:
        ai_input = {
            'nfa_number': draft_payload.get('nfa_number', 'DRAFT-NEW'),
            'title': draft_payload.get('title', ''),
            'department_name': draft_payload.get('department_name', 'N/A'),
            'project_name': draft_payload.get('project_name', 'General'),
            'vendor_name': draft_payload.get('vendor_name', ''),
            'total_amount_inr': float(draft_payload.get('total_amount', 0) or 0),
            'business_justification': draft_payload.get('business_justification', ''),
            'commercial_impact': draft_payload.get('commercial_impact', ''),
            'current_status': 'DRAFT',
            'attachment_count': int(draft_payload.get('attachment_count', 0)),
            'buyer_name': draft_payload.get('buyer_name', 'Buyer')
        }
        policies = PolicyRetriever.retrieve_relevant_policies(ai_input)
        review = LLMProvider.generate_review(ai_input, policies)
        return review
