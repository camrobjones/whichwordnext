from django.shortcuts import render
from django.http import JsonResponse
from guest_user.decorators import allow_guest_user
import json

from nwp.models import Passage, PassageToken, Profile, TokenGuess, Skip, PassageAttempt

# Create your views here.

def home(request):
    return render(request, 'nwp/home.html')

@allow_guest_user
def play(request):
    print(f"play: {request.user}")
    return render(request, 'nwp/play.html')

# @allow_guest_user
def get_sentence(request):
    print("get_sentence")
    profile, created = Profile.objects.get_or_create(user=request.user)
    # exclude passages that the user has already seen
    seen = profile.passageattempt_set.values_list('passage', flat=True)
    unseen = Passage.objects.exclude(id__in=seen)
    
    # Choose the passage with the highest proportion of guesses <= 5
    passage = unseen.order_by('-prop_guesses_5').first()

    passage_data = {
        'text': passage.text,
        'id': passage.id,
        'n_tokens': passage.n_tokens,
        'mean_surprisal': passage.mean_surprisal,
        'median_surprisal': passage.median_surprisal,
        'mean_guesses': passage.mean_guesses,
        'median_guesses': passage.median_guesses,
        'prop_guesses_5': passage.prop_guesses_5
    }

    token_data = []

    for token in passage.passagetoken_set.all():
        token_data.append({
            'token': token.token,
            'index': token.index,
            'id': token.id,
            'gpt2_surprisal': token.gpt2_surprisal,
            'gpt2_guesses': token.gpt2_guesses
        })
    
    # ensure tokens are sorted by index
    token_data.sort(key=lambda x: x['index'])

    passage_attempt = PassageAttempt(
        profile=profile,
        passage=passage
    )

    return JsonResponse({'passage': passage_data, 'tokens': token_data})


def save_guesses(request):
    print("save_guesses")
    profile, created = Profile.objects.get_or_create(user=request.user)
    data = json.loads(request.body)
    print(data)
    passage_id = data['passage_id']
    passage = Passage.objects.get(id=passage_id)
    guess_history = data['guesses']
    status = data['status']

    print(guess_history)

    for entry in guess_history:
        print(entry)
        token = PassageToken.objects.get(id=entry['id'])
        print(token)
        for ix, guess in enumerate(entry['guesses']):
            print(ix, guess)
            token_guess = TokenGuess(
                profile=profile,
                passage_token=token,
                guess_index=ix,
                guess_token=guess
            )
            token_guess.save()

        if entry["skip"] == True:
            skip = Skip(
                profile=profile,
                passage_token=token,
                guesses=len(entry['guesses'])
            )
            skip.save()

    passage_attempt, created = PassageAttempt.objects.get_or_create(
        profile=profile,
        passage=passage
    )
    passage_attempt.status = status
    passage_attempt.save()

    return JsonResponse({'status': 'success'})

# def get_prediction(request):
#     tokens = GPT2_tokenizer("At Caltech, Geneticist Beadle has stuck close to his research as head of the school's famous biology division since 1946.", return_tensors="pt")
#     logits = GPT2(**tokens).logits

#     import torch

#     last_token_logits = logits[0, -1, :]
#     sorted_indices = torch.argsort(last_token_logits, descending=True)

#     token_probs = torch.nn.functional.softmax(last_token_logits, dim=-1)

#     for idx in sorted_indices[:20]:
#         # get probabilities of next token

#         print(f"{GPT2_tokenizer.decode(idx)}: {token_probs[idx]}")


