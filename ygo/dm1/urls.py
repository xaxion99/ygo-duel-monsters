from django.urls import path
from .views import CardListView, CardDetailView

urlpatterns = [
    path('cards/', CardListView.as_view(), name='card_list'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card_detail'),
]
