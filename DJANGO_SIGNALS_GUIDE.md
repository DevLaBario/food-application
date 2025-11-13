# Django Signals: Automatic Profile Creation Guide

## Overview
This guide explains how Django signals were implemented to automatically create a `Profile` object whenever a new `User` is created, eliminating the need for manual profile creation.

---

## What Are Django Signals?

Django signals allow certain **senders** to notify a set of **receivers** when specific actions occur. Think of them as event listeners that automatically trigger functions when database operations happen.

### Common Signal Types:
- `pre_save` - Fired before an object is saved
- `post_save` - Fired after an object is saved ✅ (We use this)
- `pre_delete` - Fired before an object is deleted
- `post_delete` - Fired after an object is deleted
- `m2m_changed` - Fired when ManyToMany relationships change

---

## Our Implementation

### Problem Statement
- Users could be created without profiles
- Manual intervention required to link User ↔ Profile
- Default profile picture wouldn't display without a profile

### Solution: Automatic Profile Creation via Signals

**File:** `users/models.py`

```python
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(
        default="profile_images/default.jpg",
        upload_to="profile_images/",
        blank=True,
        null=True,
        verbose_name="Profile Picture",
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Signal: Automatically create Profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a Profile whenever a new User is created.
    
    Parameters:
    - sender: The model class (User)
    - instance: The actual User instance that was saved
    - created: Boolean - True if a new record was created
    - **kwargs: Additional keyword arguments
    """
    if created:
        Profile.objects.create(user=instance)


# Signal: Save Profile whenever User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensures the profile is saved when the user is saved.
    Creates profile if it doesn't exist (safety net).
    """
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
```

---

## How It Works: Step-by-Step

### Execution Flow

```
1. User Registration
   ↓
2. form.save() → User object created
   ↓
3. User.save() called → Saved to database
   ↓
4. post_save signal fires
   ↓
5. Django notifies all @receiver functions listening to User.post_save
   ↓
6. create_user_profile() executes
   ↓
7. Checks if created == True (new user, not update)
   ↓
8. Profile.objects.create(user=instance)
   ↓
9. Profile automatically linked to User via OneToOneField
   ↓
10. User now has profile with default.jpg image
```

### Visual Representation

```
User Model (Django built-in)          Profile Model (Custom)
┌──────────────────────────┐          ┌──────────────────────────┐
│ id: 1                    │◄─────────│ id: 1                    │
│ username: "john"         │          │ user_id: 1 (FK)          │
│ email: "john@email.com"  │          │ image: "default.jpg"     │
│ password: (hashed)       │          │                          │
└──────────────────────────┘          └──────────────────────────┘
         ▲                                        │
         │                                        │
         └────────── OneToOneField ───────────────┘
```

---

## Testing the Implementation

### Method 1: Django Shell Test

```bash
# Activate virtual environment
& C:\Users\austin\Desktop\foodApp\vem\Scripts\Activate.ps1

# Run test
vem\Scripts\python.exe manage.py shell -c "from django.contrib.auth.models import User; from users.models import Profile; u = User.objects.create_user('testuser', 'test@test.com', 'pass123'); print(f'Profile created: {hasattr(u, \"profile\")}'); print(f'Image: {u.profile.image}'); u.delete()"
```

**Expected Output:**
```
Profile created: True
Image: profile_images/default.jpg
```

### Method 2: Registration Test

1. Start server: `python manage.py runserver`
2. Navigate to registration page
3. Create new user
4. Profile automatically created with default image

### Method 3: Admin Panel Verification

1. Create user in admin panel
2. Check Profiles section
3. Profile should exist automatically

---

## Key Components Explained

### @receiver Decorator

```python
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
```

**What it does:**
- Registers `create_user_profile()` as a listener
- Listens for `post_save` signal from `User` model
- Executes automatically when User is saved

**Parameters:**
- `sender` - The model class that sent the signal (User)
- `instance` - The actual object that was saved (the user "john")
- `created` - Boolean: True if new object, False if update
- `**kwargs` - Additional signal metadata

### OneToOneField

```python
user = models.OneToOneField(User, on_delete=models.CASCADE)
```

**Purpose:**
- Links one Profile to exactly one User
- Creates reverse relationship: `user.profile`
- `on_delete=models.CASCADE` - Delete profile when user is deleted

**Access Patterns:**
```python
# From User to Profile
user = User.objects.get(username="john")
profile = user.profile
image = user.profile.image

# From Profile to User
profile = Profile.objects.get(id=1)
username = profile.user.username
email = profile.user.email
```

---

## Real-World Applications

### 1. E-commerce: Auto-Create Shopping Cart
```python
@receiver(post_save, sender=User)
def create_shopping_cart(sender, instance, created, **kwargs):
    if created:
        ShoppingCart.objects.create(user=instance, total=0.00)
```

### 2. Blog Platform: Author Statistics
```python
@receiver(post_save, sender=User)
def create_author_stats(sender, instance, created, **kwargs):
    if created:
        AuthorStats.objects.create(
            user=instance,
            article_count=0,
            total_views=0,
            joined_date=timezone.now()
        )
```

### 3. Notification System: Welcome Email
```python
@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance,
            message=f"Welcome {instance.username}!",
            type="WELCOME"
        )
        send_mail(
            subject="Welcome!",
            message="Thanks for joining!",
            from_email="noreply@site.com",
            recipient_list=[instance.email]
        )
```

### 4. Social Media: Follow Counts
```python
@receiver(post_save, sender=Follow)
def update_follower_counts(sender, instance, created, **kwargs):
    if created:
        instance.follower.profile.following_count += 1
        instance.follower.profile.save()
        
        instance.followed.profile.followers_count += 1
        instance.followed.profile.save()
```

### 5. Inventory Management: Stock Updates
```python
@receiver(post_save, sender=Order)
def update_inventory(sender, instance, created, **kwargs):
    if created:
        for item in instance.items.all():
            product = item.product
            product.stock_quantity -= item.quantity
            product.save()
```

---

## Best Practices

### ✅ DO:
- Use signals for **side effects** (creating related objects, logging, notifications)
- Keep signal handlers **simple and fast**
- Use `if created:` to distinguish new vs. updated objects
- Add try/except blocks for safety
- Document what each signal does

### ❌ DON'T:
- Put complex business logic in signals
- Create circular dependencies (A creates B, B creates A)
- Make blocking external API calls
- Forget to import signal receivers
- Modify the instance that triggered the signal (can cause infinite loops)

---

## Troubleshooting

### Problem: Profile Not Created
**Solution:** Ensure signals are imported when Django starts
- Check that models.py is loaded
- Verify no syntax errors in signal code

### Problem: Signal Fires Twice
**Solution:** Remove duplicate `@receiver` decorators or signal connections

### Problem: "No module named 'tinymce'" Error
**Solution:** Activate virtual environment before running Django commands
```bash
& C:\Users\austin\Desktop\foodApp\vem\Scripts\Activate.ps1
```

### Problem: Existing Users Have No Profile
**Solution:** Create profiles manually in admin panel or run:
```python
# In Django shell
from django.contrib.auth.models import User
from users.models import Profile

for user in User.objects.all():
    Profile.objects.get_or_create(user=user)
```

---

## Database Relationship Types

### OneToOneField (1:1)
```python
# One User → One Profile
user = models.OneToOneField(User)
# Access: user.profile
```

### ForeignKey (1:Many)
```python
# One User → Many Orders
user = models.ForeignKey(User)
# Access: user.order_set.all()
```

### ManyToManyField (Many:Many)
```python
# Many Users ↔ Many Recipes
favorites = models.ManyToManyField(Recipe)
# Access: user.favorites.all()
```

---

## Summary

### Before Signals:
1. User created manually or via registration
2. Admin must manually create Profile
3. Link User to Profile manually
4. Default image doesn't show until profile exists

### After Signals:
1. User created (any method)
2. ✨ Profile automatically created via signal
3. ✨ Automatically linked to User
4. ✨ Default image immediately available

**Result:** Zero manual intervention, bulletproof user experience! 🎯

---

## Additional Resources

- [Django Signals Documentation](https://docs.djangoproject.com/en/stable/topics/signals/)
- [Django Model Signals Reference](https://docs.djangoproject.com/en/stable/ref/signals/#module-django.db.models.signals)
- [OneToOneField Documentation](https://docs.djangoproject.com/en/stable/ref/models/fields/#onetoonefield)

---

**Last Updated:** November 13, 2025  
**Project:** Food Application - User Profile System
