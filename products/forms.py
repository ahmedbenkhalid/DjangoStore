from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control rounded-4",
                    "rows": 4,
                    "placeholder": "Write your experience here...",
                }
            ),
            "rating": forms.HiddenInput(),
        }
