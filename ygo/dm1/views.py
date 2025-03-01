from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from .models import Card

class CardListView(ListView):
    model = Card
    context_object_name = 'cards'
    template_name = 'card_list.html'

class CardDetailView(DetailView):
    model = Card
    context_object_name = 'card'
    template_name = 'card_detail.html'

def card_list(request):
    """
    Return all Card objects as JSON.
    """
    cards = Card.objects.all()
    data = [
        {
            "id": card.id,
            "card_name": card.card_name,
            "languages": card.languages,
            "image": card.image,
            "info": card.info,
        }
        for card in cards
    ]
    return JsonResponse(data, safe=False)

def card_detail(request, pk):
    """
    Return the details of a single Card (by primary key) as JSON.
    """
    card = get_object_or_404(Card, pk=pk)
    data = {
        "id": card.id,
        "card_name": card.card_name,
        "languages": card.languages,
        "image": card.image,
        "info": card.info,
    }
    return JsonResponse(data)

