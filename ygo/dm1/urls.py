from django.urls import path
from .views import CardListView, CardDetailView, FusionListView, FusionDetailView, HomeView, deck_fusion_calculator, \
    edit_collection, fusion_calculator, card_autocomplete, fusion_search_api

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('cards/', CardListView.as_view(), name='card_list'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card_detail'),
    path("fusions/", FusionListView.as_view(), name="fusion_list"),
    path("fusion/<int:pk>/", FusionDetailView.as_view(), name="fusion_detail"),
    path('collection/', edit_collection, name='collection_edit'),
    path('collection/deck-fusion/', deck_fusion_calculator, name='deck_fusion_calculator'),
    path('collection/fusion_calculator/', fusion_calculator, name='fusion_calculator'),
    path('collection/card_autocomplete/', card_autocomplete, name='card_autocomplete'),
    path('collection/fusion_search_api/', fusion_search_api, name='fusion_search_api'),
]
