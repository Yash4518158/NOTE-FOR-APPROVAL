from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authentication.models import NFARequest, SystemUser
from authentication.ai.services.nfa_review_service import NFAReviewService
from authentication.ai.services.approval_predictor import ApprovalPredictor
import logging

logger = logging.getLogger(__name__)

class AIReviewNFAView(APIView):
    """
    POST /api/ai/nfa-review/<nfa_id>/
    Or POST /api/ai/nfa-review/ with draft payload in body.
    Advisory AI RAG Review endpoint (Does NOT modify NFA, status, or workflow state).
    """
    def post(self, request, pk=None):
        try:
            if pk and pk != 'draft':
                nfa = NFARequest.objects.filter(nfa_request_id=pk).first()
                if not nfa:
                    return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

                review_data = NFAReviewService.review_nfa(nfa)
                return Response({
                    'isSuccess': True,
                    'review': review_data
                })

            draft_payload = request.data
            review_data = NFAReviewService.review_draft_payload(draft_payload)
            return Response({
                'isSuccess': True,
                'review': review_data
            })

        except Exception as e:
            logger.error(f"[AI_REVIEW_VIEW_ERROR] {str(e)}")
            return Response({
                'isSuccess': False,
                'message': 'Local AI review service is temporarily unavailable.'
            }, status=status.HTTP_200_OK)


class AIApprovalPredictionView(APIView):
    """
    GET /api/ai/approval-prediction/<nfa_id>/
    Returns approval probability percentage (0-100%) and predictive risk breakdown for approvers.
    """
    def get(self, request, pk):
        try:
            nfa = NFARequest.objects.filter(nfa_request_id=pk).first()
            if not nfa:
                return Response({'isSuccess': False, 'message': 'NFA Request not found.'}, status=status.HTTP_404_NOT_FOUND)

            prediction = ApprovalPredictor.predict_approval_probability(nfa)
            return Response({
                'isSuccess': True,
                'prediction': prediction
            })
        except Exception as e:
            logger.error(f"[AI_PREDICTION_VIEW_ERROR] {str(e)}")
            return Response({
                'isSuccess': False,
                'message': 'Failed to calculate approval prediction.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
