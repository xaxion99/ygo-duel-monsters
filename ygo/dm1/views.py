from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Value, ExpressionWrapper, F, IntegerField, Case, When
from django.db.models.functions import StrIndex, Substr, Cast
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView
from .models import Card, Fusion, CardCollection, FusionMaterialGroup


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
    # Ensure an entry exists for every card for this user.
    all_cards = Card.objects.all()
    for card in all_cards:
        CardCollection.objects.get_or_create(user=user, card=card, defaults={'quantity': 0})

    # Base queryset for this user's card collection.
    qs = CardCollection.objects.filter(user=user).select_related('card', 'card__card_info')

    # First, apply filtering by owned cards.
    filter_param = request.GET.get('filter', 'all')
    if filter_param == 'owned':
        qs = qs.filter(quantity__gte=1)

    # Next, get sort parameters.
    sort_param = request.GET.get('sort', 'card__card_info__number')
    order = request.GET.get('order', 'asc')

    # For sorting by ATK or DEF, annotate computed fields.
    if sort_param in ['atk', 'def']:
        qs = qs.annotate(
            slash_pos=StrIndex('card__card_info__atk_def', Value(' / '))
        ).annotate(
            atk_str=Substr('card__card_info__atk_def', 1,
                           ExpressionWrapper(F('slash_pos') - Value(1), output_field=IntegerField())),
            atk=Cast('atk_str', IntegerField()),
            def_str=Substr('card__card_info__atk_def',
                           ExpressionWrapper(F('slash_pos') + Value(3), output_field=IntegerField()), Value(10)),
            defense=Cast('def_str', IntegerField())
        )
        if sort_param == 'atk':
            qs = qs.annotate(
                missing_atk=Case(
                    When(card__card_info__atk_def='', then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
            if order == 'desc':
                qs = qs.order_by('missing_atk', '-atk')
            else:
                qs = qs.order_by('-missing_atk', 'atk')
        else:  # sort_param == 'def'
            qs = qs.annotate(
                missing_def=Case(
                    When(card__card_info__atk_def='', then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
            if order == 'desc':
                qs = qs.order_by('missing_def', '-defense')
            else:
                qs = qs.order_by('-missing_def', 'defense')
    else:
        # For other fields, apply ordering directly.
        if order == 'desc':
            qs = qs.order_by('-' + sort_param)
        else:
            qs = qs.order_by(sort_param)

    # Create a ModelFormSet for editing the quantity field.
    CollectionFormSet = modelformset_factory(
        CardCollection,
        fields=('quantity',),
        extra=0
    )

    if request.method == 'POST':
        formset = CollectionFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            return redirect('collection_edit')
        else:
            messages.error(request, "There was an error updating your collection. Please try again.")
    else:
        formset = CollectionFormSet(queryset=qs)

    context = {
        'formset': formset,
        'filter': filter_param,
        'current_sort': sort_param,
        'order': order,
    }
    return render(request, 'collection_edit.html', context)

@login_required
def deck_fusion_calculator(request):
    # Get IDs of cards the user owns (with quantity >= 1)
    owned_card_ids = set(
        CardCollection.objects.filter(user=request.user, quantity__gte=1)
        .values_list('card__pk', flat=True)
    )

    # Build a set of fusion result card IDs that the user owns.
    owned_result_cards = set(
        Fusion.objects.filter(result_card__pk__in=owned_card_ids)
        .values_list('result_card__pk', flat=True)
    )

    possible_fusions = []
    secondary_possible_fusions = []

    # Primary fusions: user must own at least one card from each required material group.
    for fusion in Fusion.objects.prefetch_related('material_groups'):
        for group in fusion.material_groups.all():
            material1_owned = group.material1.filter(pk__in=owned_card_ids).first()
            material2_owned = group.material2.filter(pk__in=owned_card_ids).first()
            if material1_owned and material2_owned:
                possible_fusions.append({
                    'fusion': fusion,
                    'material1': material1_owned,
                    'material2': material2_owned,
                    'result': fusion.result_card,
                })

    # Secondary fusions:
    # Check if any card in a fusion’s material group is also in the set of owned fusion result cards.
    for fusion in Fusion.objects.prefetch_related('material_groups'):
        for group in fusion.material_groups.all():
            # Option 1: A card from Material1 is a fusion result that the user owns
            mat1_candidate = group.material1.filter(pk__in=owned_result_cards).first()
            if mat1_candidate:
                other_owned = group.material2.filter(pk__in=owned_card_ids).first()
                if other_owned:
                    secondary_possible_fusions.append({
                        'fusion': fusion,
                        'material1': mat1_candidate,
                        'material2': other_owned,
                        'result': fusion.result_card,
                    })
            # Option 2: A card from Material2 is a fusion result that the user owns
            mat2_candidate = group.material2.filter(pk__in=owned_result_cards).first()
            if mat2_candidate:
                other_owned = group.material1.filter(pk__in=owned_card_ids).first()
                if other_owned:
                    secondary_possible_fusions.append({
                        'fusion': fusion,
                        'material1': other_owned,
                        'material2': mat2_candidate,
                        'result': fusion.result_card,
                    })

    context = {
        'possible_fusions': possible_fusions,
        'secondary_possible_fusions': secondary_possible_fusions,
    }
    return render(request, 'deck_fusion_calculator.html', context)


@login_required
def fusion_calculator(request):
    # Render the page; AJAX will handle fusion lookup.
    return render(request, 'fusion_calculator.html')


# --- Card Autocomplete AJAX ---
@login_required
def card_autocomplete(request):
    term = request.GET.get('term', '')
    # Return at most 10 matching cards
    cards = Card.objects.filter(card_name__icontains=term)[:10]
    results = [
        {'id': card.id, 'label': card.card_name, 'value': card.card_name}
        for card in cards
    ]
    return JsonResponse(results, safe=False)


# --- Fusion Search AJAX ---
@login_required
def fusion_search_api(request):
    """
    Expects a GET parameter 'cards' containing comma-separated card IDs.
    Returns JSON with two lists: 'primary_fusions' and 'secondary_fusions'.
    Each fusion contains:
      - fusion_number, fusion_name
      - material1: {id, name, atk_def, detail_url}
      - material2: {id, name, atk_def, detail_url}
      - result: {id, name, atk_def, detail_url}
    """
    card_ids_str = request.GET.get('cards', '')
    if not card_ids_str:
        return JsonResponse({'primary_fusions': [], 'secondary_fusions': []})

    try:
        card_ids = [int(x) for x in card_ids_str.split(',') if x.isdigit()]
    except ValueError:
        card_ids = []

    primary_fusions = []
    secondary_fusions = []

    # Primary fusions: Check if any Fusion has a material group where
    # at least one card from material1 AND one card from material2 is in the given list.
    for fusion in Fusion.objects.prefetch_related('material_groups'):
        for group in fusion.material_groups.all():
            mat1 = group.material1.filter(pk__in=card_ids).first()
            mat2 = group.material2.filter(pk__in=card_ids).first()
            if mat1 and mat2:
                primary_fusions.append({
                    'fusion_number': fusion.number,
                    'fusion_name': fusion.name,
                    'material1': {
                        'id': mat1.id,
                        'name': mat1.card_name,
                        'atk_def': mat1.card_info.atk_def if hasattr(mat1, 'card_info') else '',
                        'detail_url': reverse('card_detail', args=[mat1.id]),
                    },
                    'material2': {
                        'id': mat2.id,
                        'name': mat2.card_name,
                        'atk_def': mat2.card_info.atk_def if hasattr(mat2, 'card_info') else '',
                        'detail_url': reverse('card_detail', args=[mat2.id]),
                    },
                    'result': {
                        'id': fusion.result_card.id if fusion.result_card else None,
                        'name': fusion.result_card.card_name if fusion.result_card else '',
                        'atk_def': fusion.result_card.card_info.atk_def if fusion.result_card and hasattr(
                            fusion.result_card, 'card_info') else '',
                        'detail_url': reverse('card_detail',
                                              args=[fusion.result_card.id]) if fusion.result_card else '',
                    }
                })
                break  # break inner loop if fusion found

    # Secondary fusions: Check if any fusion's result card is also among the selected cards
    # and can act as one of the materials.
    for fusion in Fusion.objects.prefetch_related('material_groups'):
        for group in fusion.material_groups.all():
            # Option 1: Check if any card in material1 is also in the selected list and is a fusion result
            mat1_candidate = group.material1.filter(pk__in=card_ids).first()
            if mat1_candidate:
                mat2 = group.material2.filter(pk__in=card_ids).first()
                if mat2:
                    secondary_fusions.append({
                        'fusion_number': fusion.number,
                        'fusion_name': fusion.name,
                        'material1': {
                            'id': mat1_candidate.id,
                            'name': mat1_candidate.card_name,
                            'atk_def': mat1_candidate.card_info.atk_def if hasattr(mat1_candidate, 'card_info') else '',
                            'detail_url': reverse('card_detail', args=[mat1_candidate.id]),
                        },
                        'material2': {
                            'id': mat2.id,
                            'name': mat2.card_name,
                            'atk_def': mat2.card_info.atk_def if hasattr(mat2, 'card_info') else '',
                            'detail_url': reverse('card_detail', args=[mat2.id]),
                        },
                        'result': {
                            'id': fusion.result_card.id if fusion.result_card else None,
                            'name': fusion.result_card.card_name if fusion.result_card else '',
                            'atk_def': fusion.result_card.card_info.atk_def if fusion.result_card and hasattr(
                                fusion.result_card, 'card_info') else '',
                            'detail_url': reverse('card_detail',
                                                  args=[fusion.result_card.id]) if fusion.result_card else '',
                        }
                    })
                    break
            # Option 2: Check vice-versa for material2 candidate.
            mat2_candidate = group.material2.filter(pk__in=card_ids).first()
            if mat2_candidate:
                mat1 = group.material1.filter(pk__in=card_ids).first()
                if mat1:
                    secondary_fusions.append({
                        'fusion_number': fusion.number,
                        'fusion_name': fusion.name,
                        'material1': {
                            'id': mat1.id,
                            'name': mat1.card_name,
                            'atk_def': mat1.card_info.atk_def if hasattr(mat1, 'card_info') else '',
                            'detail_url': reverse('card_detail', args=[mat1.id]),
                        },
                        'material2': {
                            'id': mat2_candidate.id,
                            'name': mat2_candidate.card_name,
                            'atk_def': mat2_candidate.card_info.atk_def if hasattr(mat2_candidate, 'card_info') else '',
                            'detail_url': reverse('card_detail', args=[mat2_candidate.id]),
                        },
                        'result': {
                            'id': fusion.result_card.id if fusion.result_card else None,
                            'name': fusion.result_card.card_name if fusion.result_card else '',
                            'atk_def': fusion.result_card.card_info.atk_def if fusion.result_card and hasattr(
                                fusion.result_card, 'card_info') else '',
                            'detail_url': reverse('card_detail',
                                                  args=[fusion.result_card.id]) if fusion.result_card else '',
                        }
                    })
                    break

    return JsonResponse({
        'primary_fusions': primary_fusions,
        'secondary_fusions': secondary_fusions,
    })

