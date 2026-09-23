class NFAReviewOutputSchema:
    """Schema normalizer for structured AI review outputs"""

    @staticmethod
    def validate_and_normalize(raw_data: dict) -> dict:
        if not isinstance(raw_data, dict):
            raw_data = {}

        score = raw_data.get('readiness_score', 80)
        try:
            score = int(score)
            score = max(0, min(100, score))
        except (ValueError, TypeError):
            score = 80

        summary = str(raw_data.get('summary', 'NFA Request audit completed.'))
        issues = raw_data.get('issues', [])
        if not isinstance(issues, list):
            issues = []

        norm_issues = []
        for iss in issues:
            if isinstance(iss, dict):
                norm_issues.append({
                    'severity': str(iss.get('severity', 'medium')).lower(),
                    'field': str(iss.get('field', 'general')),
                    'title': str(iss.get('title', 'Compliance Note')),
                    'description': str(iss.get('description', '')),
                    'recommendation': str(iss.get('recommendation', 'Review NFA documentation.'))
                })

        strengths = raw_data.get('strengths', [])
        if not isinstance(strengths, list):
            strengths = []
        norm_strengths = []
        for st in strengths:
            if isinstance(st, dict):
                norm_strengths.append({
                    'field': str(st.get('field', 'general')),
                    'description': str(st.get('description', ''))
                })

        recs = raw_data.get('recommendations', [])
        if not isinstance(recs, list):
            recs = []
        norm_recs = [str(r) for r in recs]

        return {
            'readiness_score': score,
            'summary': summary,
            'issues': norm_issues,
            'strengths': norm_strengths,
            'recommendations': norm_recs
        }
