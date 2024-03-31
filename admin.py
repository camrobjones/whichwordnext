from django.contrib import admin

# Register your models here.

from .models import Passage

class PassageAdmin(admin.ModelAdmin):
    list_display = ["id","corpus", "category", "fileid",  "n_tokens",  "prop_guesses_5", "mean_surprisal", "median_surprisal", "mean_guesses", "median_guesses",]

admin.site.register(Passage, PassageAdmin)