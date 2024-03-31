import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import re
import random
import nltk
from nltk.corpus import brown

from nwp.models import Passage, PassageToken

GPT2_tokenizer = AutoTokenizer.from_pretrained("gpt2")
GPT2 = AutoModelForCausalLM.from_pretrained("gpt2")
BROWN = brown.paras()


def get_sentence():
    # Sample a random sentence from the brown corpus
    para = random.choice(BROWN)
    # remove spaces before punctuation
    para_text = ' '.join([' '.join(sent) for sent in para])
    para_text = re.sub(r'\s([?.!",](?:\s|$))', r'\1', para_text)

    return para_text

def get_surprisals(sent):
    inputs = GPT2_tokenizer(sent, return_tensors="pt")
    logits = GPT2(**inputs).logits

    tokens = GPT2_tokenizer.tokenize(sent)

    surprisals = []
    guesses = []

    for idx, token in enumerate(tokens[1:]):
        token_id = GPT2_tokenizer.encode(token.replace('Ġ', ' '))[0]
        token_logits = logits[0][idx]
        token_probs = torch.nn.functional.softmax(token_logits, dim=-1)
        token_surprisal = -torch.log2(token_probs[token_id]).item()
        surprisals.append(token_surprisal)
        token_guesses = torch.where(torch.argsort(token_probs, descending=True) == token_id)[0].item()
        guesses.append(token_guesses)

        # print(f"{token}: {token_surprisal} {token_guesses}")

    max_surprisal = max(surprisals)
    max_guesses = max(guesses)
    mean_surprisal = sum(surprisals) / len(surprisals)
    mean_guesses = sum(guesses) / len(guesses)
    median_guesses = sorted(guesses)[len(guesses) // 2]
    # get 85th centile of guesses
    guesses_85 = sorted(guesses)[int(len(guesses) * 0.85)]

     # Get median in first 25% of tokens
    first_quarter_guesses = sorted(guesses[:len(guesses) // 4])
    first_quarter_median_guesses = first_quarter_guesses[len(first_quarter_guesses) // 2]
    first_quarter_guesses_85 = first_quarter_guesses[int(len(first_quarter_guesses) * 0.85)]

    # Proportion of guesses <= 5
    guesses_5 = len([g for g in guesses if g <= 5]) / len(guesses)
    fq_guesses_5 = len([g for g in first_quarter_guesses if g <= 5]) / len(first_quarter_guesses)

    # print(f"Max surprisal: {max_surprisal} Max guesses: {max_guesses}")
    # print(f"Mean surprisal: {mean_surprisal} Mean guesses: {mean_guesses}")
    # print(f"Median guesses: {median_guesses}, 85th centile guesses: {guesses_85}")
    # print(f"First quarter median guesses: {first_quarter_median_guesses}, 85th centile guesses: {first_quarter_guesses_85}")
    # print(f"Proportion of guesses <= 5: {guesses_5}, FQ: {fq_guesses_5}")

    return surprisals, guesses

# good_paras = []

# from tqdm import tqdm

# for cat in brown.categories()[6:]:
#     fileids = brown.fileids(categories=cat)
#     print("-" * 20)
#     print(cat, len(fileids))
#     print("-" * 20)
#     for fileid in fileids:
#         paras = brown.paras(fileid)
#         print(fileid, len(paras))
#         for para in tqdm(paras):
#             para_text = ' '.join([' '.join(sent) for sent in para])
#             para_text = re.sub(r'\s([?.!",](?:\s|$))', r'\1', para_text)
#             try:
#                 s, g, m, g5 = get_surprisals(para_text)
#             except:
#                 continue
#             if m <= 3 and g5 >= 0.7:
#                 print(m, round(g5, 3))
#                 good_paras.append((cat, fileid, para_text))


# s = get_sentence()
# print(s)

# s.split()[:len(s.split()) // 4]

# all_paras = len(brown.paras())
# cumulative = 0
# for cat in brown.categories():
#     fileids = brown.fileids(categories=cat)
#     paras = brown.paras(categories=cat)
#     cumulative += len(paras)
#     cumprop = round(cumulative / all_paras, 2)
#     print(cat, len(paras), cumprop)

def clean_text(text):
    text = re.sub(r'\s([?.!",](?:\s|$))', r'\1', text)
    text = re.sub(r'`` ', '"', text)
    # text = re.sub(" ?''", '"', text)
    # Replace opening quotes
    text = re.sub(r'``\s?', '"', text)
    # Replace closing quotes
    text = re.sub(r'\s?\'\'', '"', text)
    text = re.sub("(\? ?)+", "?", text)
    return text

def store_passage(corpus, category, fileid, index, text):
    tokens = GPT2_tokenizer.tokenize(text)
    tokens = [t.replace('Ġ', ' ') for t in tokens]
    spl, g = get_surprisals(text)
    mean_surprisal = sum(spl) / len(spl)
    median_surprisal = sorted(spl)[len(spl) // 2]
    mean_guesses = sum(g) / len(g)
    median_guesses = sorted(g)[len(g) // 2]
    prop_guesses_5 = len([guess for guess in g if guess <= 5]) / len(g)

    p = Passage(
        text=text,
        corpus=corpus,
        category=category,
        fileid=fileid,
        index=index,
        n_tokens=len(tokens),
        mean_surprisal=mean_surprisal,
        median_surprisal=median_surprisal,
        mean_guesses=mean_guesses,
        median_guesses=median_guesses,
        prop_guesses_5=prop_guesses_5
    )
    p.save()

    # store first token
    pt = PassageToken(
        passage=p,
        token=tokens[0],
        index=0,
        gpt2_surprisal=None,
        gpt2_guesses=None
    )
    pt.save()

    for idx, token in enumerate(tokens[1:]):
        pt = PassageToken(
            passage=p,
            token=token,
            index=idx + 1,
            gpt2_surprisal=spl[idx],
            gpt2_guesses=g[idx]
        )
        pt.save()

    return p

# delete all passages & tokens
Passage.objects.all().delete()
PassageToken.objects.all().delete()

import json

# with open('nwp/good_paras.json', 'w') as f:
#     json.dump(good_paras, f, indent=4)

reloaded_paras = json.load(open('nwp/good_paras.json'))

# filter out government and paras w/ < 10 or > 100 tokens.

reloaded_paras = [para for para in reloaded_paras if para[0] != 'government' and 10 <= len(para[2].split()) <= 100]



for para in reloaded_paras:
    text = para[2]
    text = clean_text(text)
    p = store_passage('brown', para[0], para[1], 0, text)
    PassageTokens = PassageToken.objects.all()
    for pt in PassageToken.objects.all():
        spl = pt.gpt2_surprisal
        guesses = pt.gpt2_guesses
        print(f"{pt.token}: {spl} {guesses}")