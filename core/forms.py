from django import forms

from .models import HomePageSection, ProductItem
from .models import PlanItem


class HomePageSectionForm(forms.ModelForm):
    class Meta:
        model = HomePageSection
        fields = ["title", "subtitle", "is_active", "display_order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subtitle": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "display_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ProductItemForm(forms.ModelForm):
    class Meta:
        model = ProductItem
        fields = [
            "name",
            "description",
            "price",
            "image",
            "image_url",
            "display_order",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "image_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "Optional: external image URL"}),
            "display_order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class PlanItemForm(forms.ModelForm):
    class Meta:
        model = PlanItem
        fields = [
            "icon",
            "title",
            "description",
            "amount",
            "display_order",
            "is_active",
        ]
        widgets = {
            "icon": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 👥 or fa-icon text"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "amount": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 6% or ₹200"}),
            "display_order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

