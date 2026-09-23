import json

class NFAPromptBuilder:
    SYSTEM_PROMPT = """You are an expert AI procurement auditor reviewing a Note for Approval (NFA) request against Company Procurement Policies (RAG Context). 
Your role is purely ADVISORY. Identify incomplete, vague, inconsistent, or non-compliant information and provide recommendations.

RULES:
1. Output MUST be strictly valid JSON complying with this schema:
{
  "readiness_score": integer (0 to 100),
  "summary": "Short summary of overall NFA quality and policy compliance",
  "issues": [
    {
      "severity": "high" | "medium" | "low",
      "field": "business_justification" | "commercial_impact" | "vendor_name" | "total_amount" | "attachments" | "policy_compliance",
      "title": "Short title",
      "description": "Explanation of issue or policy clause mismatch",
      "recommendation": "Actionable advice for buyer"
    }
  ],
  "strengths": [
    {
      "field": "field_name",
      "description": "Explanation of strength"
    }
  ],
  "recommendations": [
    "General advice"
  ]
}
2. Do NOT invent missing facts. Base review on provided NFA details and RAG policy context.
"""

    @staticmethod
    def build_user_prompt(nfa_review_input: dict, policy_clauses: list = None) -> str:
        policy_text = ""
        if policy_clauses and len(policy_clauses) > 0:
            policy_text = "\n\nCOMPANY PROCUREMENT POLICY CLAUSES (LOCAL RAG CONTEXT):\n"
            for p in policy_clauses:
                policy_text += f"- [{p.get('section_title', 'Policy')}]: {p.get('clause_text', '')}\n"

        return f"""Please conduct a RAG-enhanced advisory review on the following NFA Request:

{json.dumps(nfa_review_input, indent=2)}
{policy_text}

Analyze the NFA for:
1. Completeness & Clarity of Business Justification
2. Commercial Impact & Cost ROI
3. Compliance with Company Procurement Policies (RAG Context)
4. Vendor & Attachment readiness

Return strictly valid JSON matching the system prompt schema."""
