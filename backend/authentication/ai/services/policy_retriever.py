from authentication.models import PolicyChunk
from authentication.ai.services.vector_store_service import VectorStoreService
import logging

logger = logging.getLogger(__name__)

class PolicyRetriever:
    """RAG Policy Retrieval Engine using local Vector Search (ChromaDB) + Database Chunk Fallbacks"""

    @staticmethod
    def retrieve_relevant_policies(nfa_input: dict) -> list:
        try:
            amount = float(nfa_input.get('total_amount_inr', 0) or 0)
            dept = str(nfa_input.get('department_name', '')).lower()
            title = str(nfa_input.get('title', '')).lower()
            just = str(nfa_input.get('business_justification', '')).lower()
            impact = str(nfa_input.get('commercial_impact', '')).lower()
            vendor = str(nfa_input.get('vendor_name', '')).lower()

            text_query = f"{title} {just} {impact} {dept} {vendor} amount {amount}"

            # 1. Vector Semantic Similarity Search via ChromaDB
            matched_clauses = VectorStoreService.search_policies(text_query, n_results=4)

            # 2. Database PolicyChunk fallback / additional filtering if DB records exist
            try:
                active_chunks = PolicyChunk.objects.filter(is_active=True)
                for chunk in active_chunks:
                    min_lim = float(chunk.min_amount_limit or 0)
                    max_lim = float(chunk.max_amount_limit or 999999999)
                    
                    if min_lim <= amount <= max_lim:
                        kw_list = [k.strip().lower() for k in (chunk.keywords or '').split(',') if k.strip()]
                        if any(kw in text_query for kw in kw_list):
                            matched_clauses.append({
                                'clause_id': str(chunk.chunk_id),
                                'section_title': chunk.section_title,
                                'clause_text': chunk.chunk_text
                            })
            except Exception as dbe:
                logger.debug(f"[PolicyRetriever] DB Chunk lookup note: {str(dbe)}")

            # Deduplicate by section_title
            seen = set()
            unique_clauses = []
            for c in matched_clauses:
                st = c.get('section_title', '')
                if st not in seen:
                    seen.add(st)
                    unique_clauses.append(c)

            return unique_clauses

        except Exception as e:
            logger.error(f"[RAG_RETRIEVER_ERROR] {str(e)}")
            return []
