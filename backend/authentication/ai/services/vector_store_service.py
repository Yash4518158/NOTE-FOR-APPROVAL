import os
import logging
import chromadb
from django.conf import settings

logger = logging.getLogger(__name__)

# Default Company Procurement Policies to seed if vector DB is empty
DEFAULT_POLICIES = [
    {
        "id": "policy_bidding_1",
        "section_title": "Competitive Bidding Requirements (Policy Section 3.1)",
        "chunk_text": "All procurement requests with a total estimated value exceeding ₹50,000 INR must include at least three (3) independent, written competitive supplier quotations attached to the NFA. If fewer than 3 quotes are submitted, a formal Single Source Approval Form signed by the Department Head is mandatory.",
        "min_amount": 50000.0,
        "max_amount": 999999999.0,
        "keywords": "bidding, quotation, quotes, single source, supplier, 50000"
    },
    {
        "id": "policy_doa_2",
        "section_title": "Delegation of Authority (DOA) Financial Approval Limits (Policy Section 4.2)",
        "chunk_text": "Financial Approval Matrix: Purchases up to ₹100,000 INR require Level 1 Department Manager approval. Purchases between ₹100,001 and ₹500,000 INR require Level 2 Vice President approval. Purchases exceeding ₹500,000 INR mandate Level 3 CFO or Managing Director approval in sequential order.",
        "min_amount": 100000.0,
        "max_amount": 999999999.0,
        "keywords": "doa, approval limit, cfo, vice president, financial limit, 500000"
    },
    {
        "id": "policy_it_3",
        "section_title": "IT Equipment & Software Procurement Protocol (Policy Section 5.4)",
        "chunk_text": "All IT hardware, software licenses, cloud infrastructure, and server procurement requests must obtain written technical specification clearance from the IT Security & Architecture Team prior to NFA submission.",
        "min_amount": 0.0,
        "max_amount": 999999999.0,
        "keywords": "it, software, hardware, server, cloud, license, security"
    },
    {
        "id": "policy_commercial_4",
        "section_title": "Commercial Justification & Cost ROI (Policy Section 2.3)",
        "chunk_text": "Every NFA must clearly document a quantifiable business justification and commercial impact, detailing cost savings, ROI timeline, or operational risk mitigated. Placeholder text or short non-descriptive summaries will result in request rejection.",
        "min_amount": 0.0,
        "max_amount": 999999999.0,
        "keywords": "justification, commercial impact, roi, savings, cost"
    }
]

class VectorStoreService:
    """Local On-Premise Vector Database Service powered by ChromaDB"""
    _client = None
    _collection = None

    @classmethod
    def _get_collection(cls):
        if cls._collection is None:
            try:
                db_dir = getattr(settings, 'VECTOR_STORE_DIR', os.path.join(settings.BASE_DIR, 'vector_store'))
                os.makedirs(db_dir, exist_ok=True)
                cls._client = chromadb.PersistentClient(path=db_dir)
                cls._collection = cls._client.get_or_create_collection(
                    name="nfa_policy_clauses",
                    metadata={"hnsw:space": "cosine"}
                )
                # Seed default policies if empty
                if cls._collection.count() == 0:
                    cls.seed_default_policies()
            except Exception as e:
                logger.error(f"[VectorStoreService] Initialization error: {str(e)}")
                return None
        return cls._collection

    @classmethod
    def seed_default_policies(cls):
        try:
            col = cls._collection
            if not col:
                return
            ids = [p["id"] for p in DEFAULT_POLICIES]
            documents = [f"[{p['section_title']}]: {p['chunk_text']}" for p in DEFAULT_POLICIES]
            metadatas = [
                {
                    "section_title": p["section_title"],
                    "keywords": p["keywords"],
                    "min_amount": p["min_amount"],
                    "max_amount": p["max_amount"]
                }
                for p in DEFAULT_POLICIES
            ]
            col.add(ids=ids, documents=documents, metadatas=metadatas)
            logger.info(f"[VectorStoreService] Successfully seeded {len(ids)} policy clauses into local vector DB.")
        except Exception as e:
            logger.error(f"[VectorStoreService] Error seeding default policies: {str(e)}")

    @classmethod
    def search_policies(cls, query_text: str, n_results: int = 3) -> list:
        """Perform semantic vector similarity search against local ChromaDB"""
        try:
            col = cls._get_collection()
            if not col or col.count() == 0:
                return []

            results = col.query(
                query_texts=[query_text],
                n_results=min(n_results, col.count())
            )

            matched_clauses = []
            if results and results.get('documents') and len(results['documents']) > 0:
                docs = results['documents'][0]
                metas = results['metadatas'][0] if results.get('metadatas') else []
                ids = results['ids'][0] if results.get('ids') else []

                for i in range(len(docs)):
                    meta = metas[i] if i < len(metas) else {}
                    matched_clauses.append({
                        'clause_id': ids[i] if i < len(ids) else f"chunk_{i}",
                        'section_title': meta.get('section_title', 'Procurement Policy Clause'),
                        'clause_text': docs[i]
                    })
            return matched_clauses
        except Exception as e:
            logger.error(f"[VectorStoreService] Vector search error: {str(e)}")
            return []
