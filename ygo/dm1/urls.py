from django.urls import path
from .views import CardListView, CardDetailView, FusionListView, FusionDetailView, edit_collection, HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('cards/', CardListView.as_view(), name='card_list'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card_detail'),
    path("fusions/", FusionListView.as_view(), name="fusion_list"),
    path("fusion/<int:pk>/", FusionDetailView.as_view(), name="fusion_detail"),
    path('collection/', edit_collection, name='collection_edit'),
]
