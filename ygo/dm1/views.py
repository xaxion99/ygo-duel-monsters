from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, TemplateView
from .models import Card, Fusion, CardCollection

class HomeView(TemplateView):
    template_name = "home.html"

class CardListView(ListView):
    model = Card
    context_object_name = 'cards'
    template_name = 'card_list.html'

class CardDetailView(DetailView):
    model = Card
    template_name = "card_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve ordered list of card IDs (or another field for ordering)
        card_ids = list(Card.objects.order_by('pk').values_list('pk', flat=True))
        current_id = self.object.pk
        try:
            current_index = card_ids.index(current_id)
        except ValueError:
            current_index = 0

        prev_card = None
        next_card = None
        if current_index > 0:
            prev_card = Card.objects.get(pk=card_ids[current_index - 1])
        if current_index < len(card_ids) - 1:
            next_card = Card.objects.get(pk=card_ids[current_index + 1])

        context['prev_card'] = prev_card
        context['next_card'] = next_card
        return context

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
    card = get_object_or_404(Card, pk=pk)
    prev_card = Card.objects.filter(pk__lt=card.pk).order_by('-pk').first()
    next_card = Card.objects.filter(pk__gt=card.pk).order_by('pk').first()
    return render(request, "card_detail.html", {
        "card": card,
        "prev_card": prev_card,
        "next_card": next_card,
    })


class FusionListView(ListView):
    model = Fusion
    template_name = "fusion_list.html"
    context_object_name = "fusions"

    def get_queryset(self):
        return Fusion.objects.order_by('number')

class FusionDetailView(DetailView):
    model = Fusion
    template_name = "fusion_detail.html"  # Adjust to your actual template name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fusion_numbers = list(Fusion.objects.order_by('number').values_list('number', flat=True))
        current_number = self.object.number
        try:
            current_index = fusion_numbers.index(current_number)
        except ValueError:
            current_index = 0

        prev_fusion = None
        next_fusion = None
        if current_index > 0:
            prev_number = fusion_numbers[current_index - 1]
            prev_fusion = Fusion.objects.get(number=prev_number)
        if current_index < len(fusion_numbers) - 1:
            next_number = fusion_numbers[current_index + 1]
            next_fusion = Fusion.objects.get(number=next_number)

        context['prev_fusion'] = prev_fusion
        context['next_fusion'] = next_fusion
        return context

def fusion_detail(request, pk):
    fusion = get_object_or_404(Fusion, pk=pk)
    prev_fusion = Fusion.objects.filter(pk__lt=fusion.pk).order_by('-pk').first()
    next_fusion = Fusion.objects.filter(pk__gt=fusion.pk).order_by('pk').first()
    return render(request, "fusion_detail.html", {
        "fusion": fusion,
        "prev_fusion": prev_fusion,
        "next_fusion": next_fusion,
    })


@login_required
def edit_collection(request):
    user = request.user
    # Ensure an entry exists for every card for this user
    all_cards = Card.objects.all()
    for card in all_cards:
        CardCollection.objects.get_or_create(user=user, card=card, defaults={'quantity': 0})

    # Create a modelformset for editing quantities only
    CollectionFormSet = modelformset_factory(
        CardCollection,
        fields=('quantity',),
        extra=0
    )

    qs = CardCollection.objects.filter(user=user).select_related('card', 'card__card_info').order_by(
        'card__card_info__number')

    if request.method == 'POST':
        formset = CollectionFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            return redirect('collection_edit')
    else:
        formset = CollectionFormSet(queryset=qs)

    context = {'formset': formset}
    return render(request, 'collection_edit.html', context)
