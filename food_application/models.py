from django.db import models
from tinymce.models import HTMLField


# Create your models here.
class Item(models.Model):
    item_name = models.CharField(max_length=100)
    item_description = models.CharField(
        max_length=200, default="No description available", blank=True
    )  # Changed to CharField for short description
    item_recipe = HTMLField(
        default="<p>Recipe coming soon!</p>", blank=True
    )  # New field for full recipe with rich text
    item_price = models.IntegerField()
    item_image = models.CharField(
        max_length=500,
        default="https://theme-assets.getbento.com/sensei/cb0fd97.sensei/assets/images/catering-item-placeholder-704x520.png",
    )

    def __str__(self):
        return self.item_name
