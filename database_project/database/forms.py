from django import forms

class GlobalSearchForm(forms.Form):
    q = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            "placeholder": "Search by name, title, email, journal, conference, keyword...",
        })
    )
