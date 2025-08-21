from recommendation_service import RecommendationService


recommendation_service = RecommendationService()

query_description = "A thrilling mystery novel set in a small town with a detective protagonist."

recommendation = recommendation_service.call_model(query_description)
print(recommendation)
