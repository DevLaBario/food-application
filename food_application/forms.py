from django import forms
from .models import Item
from tinymce.widgets import TinyMCE


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "item_name",
            "item_description",
            "item_recipe",
            "item_price",
            "item_image",
        ]
        widgets = {
            "item_recipe": TinyMCE(attrs={"cols": 80, "rows": 30}),
        }
        labels = {
            "item_name": "Recipe Name",
            "item_description": "Short Description",
            "item_recipe": "Full Recipe",
            "item_price": "Price",
            "item_image": "Image URL",
        }
        help_texts = {
            "item_description": "A brief description (max 200 characters)",
            "item_recipe": "Full recipe with ingredients and instructions",
        }
