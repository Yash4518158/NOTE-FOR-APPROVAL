import os
import json
import logging
import urllib.request
from django.conf import settings
from authentication.ai.services.prompt_builder import NFAPromptBuilder
from authentication.ai.schemas.review_schema import NFAReviewOutputSchema

logger = logging.getLogger(__name__)

class LLMProvider:
    """100% Local On-Premise LLM Provider (Powered by Ollama / Local Rest API)"""

    @staticmethod
    def generate_review(nfa_review_input: dict, policies: list = None) -> dict:
        ollama_url = getattr(settings, 'OLLAMA_API_URL', 'http://127.0.0.1:11434/api/generate')
        ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:3b')

        user_prompt = NFAPromptBuilder.build_user_prompt(nfa_review_input, policies)

        # 1. Try local Ollama LLM execution first
        try:
            return LLMProvider._call_local_ollama(ollama_url, ollama_model, NFAPromptBuilder.SYSTEM_PROMPT, user_prompt, policies)
        except Exception as e:
            logger.info(f"[AI] Local Ollama server notice ({str(e)}). Using local heuristic RAG review engine.")

        # 2. Local Fallback Heuristic RAG Engine (Zero network dependency)
        return LLMProvider._heuristic_rag_review(nfa_review_input, policies)

    @staticmethod
    def _call_local_ollama(ollama_url: str, model_name: str, system_prompt: str, user_prompt: str, policies: list = None) -> dict:
        payload = {
            "model": model_name,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        req = urllib.request.Request(
            ollama_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=2) as response:

            res_data = json.loads(response.read().decode('utf-8'))

        response_text = res_data.get('response', '{}')
        raw_json = json.loads(response_text)
        res_dict = NFAReviewOutputSchema.validate_and_normalize(raw_json)
        res_dict['matched_policies'] = policies or []
        res_dict['execution_mode'] = 'LOCAL_OLLAMA'
        return res_dict

    @staticmethod
    def _heuristic_rag_review(inp: dict, policies: list = None) -> dict:
        """Local Rule-Based Heuristic RAG Engine (Guaranteed 0ms offline execution)"""
        score = 100
        issues = []
        strengths = []
        recommendations = []

        title = inp.get('title', '').strip()
        just = inp.get('business_justification', '').strip()
        impact = inp.get('commercial_impact', '').strip()
        vendor = inp.get('vendor_name', '').strip()
        amount = float(inp.get('total_amount_inr', 0) or 0)
        att_count = int(inp.get('attachment_count', 0))

        # 1. RAG Policy Compliance Check
        if policies:
            for pol in policies:
                stitle = pol.get('section_title', '')
                ctext = pol.get('clause_text', '')
                if ('Bidding' in stitle or '3' in ctext) and amount >= 50000 and att_count < 3:
                    score -= 20
                    issues.append({
                        'severity': 'high',
                        'field': 'policy_compliance',
                        'title': f"RAG Alert: {stitle}",
                        'description': f"NFA total (₹{amount:,.2f}) exceeds ₹50,000 INR limit requiring 3 vendor quotes (currently {att_count} attached).",
                        'recommendation': 'Attach at least 3 competitive vendor quotes or a Single Source Approval Form.'
                    })
                elif ('DOA' in stitle or 'Approval' in stitle) and amount >= 500000:
                    score -= 15
                    issues.append({
                        'severity': 'medium',
                        'field': 'policy_compliance',
                        'title': f"RAG Compliance: {stitle}",
                        'description': f"NFA total (₹{amount:,.2f}) exceeds ₹500,000 INR requiring Level 3 CFO approval.",
                        'recommendation': 'Ensure CFO / MD is included in approval workflow chain.'
                    })
                elif 'IT' in stitle:
                    strengths.append({
                        'field': 'policy_compliance',
                        'description': f"Matched Policy [{stitle}]: Technical specification check applied."
                    })

        # 2. Quality & Completeness Checks
        if len(just) < 15 or just.lower() in ['test', 'testing', 'n/a']:
            score -= 20
            issues.append({
                'severity': 'high',
                'field': 'business_justification',
                'title': 'Vague Business Justification',
                'description': 'The business justification is brief or contains placeholder text.',
                'recommendation': 'Elaborate on operational problem solved and request necessity.'
            })
        else:
            strengths.append({
                'field': 'business_justification',
                'description': 'Business justification details are provided.'
            })

        if len(impact) < 15 or impact.lower() in ['test', 'testing', 'n/a']:
            score -= 15
            issues.append({
                'severity': 'medium',
                'field': 'commercial_impact',
                'title': 'Incomplete Commercial ROI',
                'description': 'Commercial impact section lacks quantitative cost savings or ROI metrics.',
                'recommendation': 'Quantify expected cost savings or ROI timelines.'
            })
        else:
            strengths.append({
                'field': 'commercial_impact',
                'description': 'Commercial impact details are provided.'
            })

        if not vendor or vendor.lower() == 'test':
            score -= 10
            issues.append({
                'severity': 'medium',
                'field': 'vendor_name',
                'title': 'Vendor Name Verification',
                'description': 'Vendor name appears generic or unverified.',
                'recommendation': 'Verify official vendor name matching quotation.'
            })

        summary = (
            f"Local RAG Policy Compliance review completed ({len(policies or [])} clauses evaluated)."
            if score >= 80
            else "NFA request has minor policy compliance or documentation gaps."
        )

        recommendations.append("Ensure vendor quotations and compliance documents are attached.")
        recommendations.append("Verify department DOA approval limits prior to submission.")

        normalized = NFAReviewOutputSchema.validate_and_normalize({
            'readiness_score': max(0, score),
            'summary': summary,
            'issues': issues,
            'strengths': strengths,
            'recommendations': recommendations
        })
        normalized['matched_policies'] = policies or []
        normalized['execution_mode'] = 'LOCAL_HEURISTIC_RAG'
        return normalized
