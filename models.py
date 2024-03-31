from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class Passage(models.Model):
    text = models.TextField()
    corpus = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    fileid = models.CharField(max_length=100)
    index = models.IntegerField()

    n_tokens = models.IntegerField()
    mean_surprisal = models.FloatField()
    median_surprisal = models.FloatField()

    mean_guesses = models.FloatField()
    median_guesses = models.FloatField()
    prop_guesses_5 = models.FloatField()

    def __str__(self):
        return f"{self.corpus} ({self.category}): {self.fileid}"
    
class PassageToken(models.Model):
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    index = models.IntegerField()
    gpt2_surprisal = models.FloatField(blank=True, null=True)
    gpt2_guesses = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.passage.id} ({self.index}) - {self.token}"
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField

class TokenGuess(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    passage_token = models.ForeignKey(PassageToken, on_delete=models.CASCADE)
    guess_index = models.IntegerField()
    guess_token = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.profile.user} - {self.passage_token.passage} - {self.guess_token}"
    
class Skip(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    passage_token = models.ForeignKey(PassageToken, on_delete=models.CASCADE)
    guesses = models.IntegerField()

    def __str__(self):
        return f"{self.profile.user} - {self.passageToken}"
    

class PassageAttempt(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, default='incomplete')

    def __str__(self):
        return f"{self.profile.user} - {self.passage}"