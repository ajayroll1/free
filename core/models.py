from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from decimal import Decimal

class CustomUser(AbstractUser):
    """Custom User Model for MLM System"""
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be entered in the format: +999999999. Up to 15 digits allowed.'
    )
    
    # Profile Information
    mobile = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Mobile Number"
    )
    
    # MLM System Fields
    sponsor_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Sponsor ID"
    )
    
    sponsor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Sponsor Name"
    )
    
    # Referral ID for this user to share
    referral_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Referral ID"
    )
    
    # Account Balance
    account_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Account Balance"
    )
    
    # Account Status
    is_active_member = models.BooleanField(
        default=False,
        verbose_name="Is Active Member"
    )
    
    # Profile Photo
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        verbose_name="Profile Photo"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override groups and permissions with proper related_name
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='customuser_set'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='customuser_set'
    )
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_referral_count(self):
        """Get total referrals/downline count"""
        return Referral.objects.filter(sponsor=self).count()
    
    def get_purchase_count(self):
        """Get total product purchases"""
        return Purchase.objects.filter(user=self).count()
    
    def get_total_purchase_amount(self):
        """Get total amount spent on products"""
        purchases = Purchase.objects.filter(user=self)
        total = sum(p.total_amount for p in purchases)
        return Decimal(str(total))
    
    def generate_referral_id(self):
        """Generate a unique referral ID in format: MLM + 6 random alphanumeric"""
        import random
        import string
        
        # Generate 6 random characters and numbers
        characters = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(characters, k=6))
        referral_id = f"MLM{random_part}"
        
        # Ensure it's unique
        while CustomUser.objects.filter(referral_id=referral_id).exists():
            random_part = ''.join(random.choices(characters, k=6))
            referral_id = f"MLM{random_part}"
        
        return referral_id


class Product(models.Model):
    """Product Model"""
    name = models.CharField(max_length=255, verbose_name="Product Name")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
    
    def __str__(self):
        return self.name


class Purchase(models.Model):
    """Product Purchase Model"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-purchase_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name}"


class Referral(models.Model):
    """Referral/Downline Model"""
    sponsor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referrals')
    referred_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='referred_by')
    referral_date = models.DateTimeField(auto_now_add=True)
    commission_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    class Meta:
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"
        unique_together = ['sponsor', 'referred_user']
    
    def __str__(self):
        return f"{self.sponsor.email} referred {self.referred_user.email}"


class Withdrawal(models.Model):
    """Withdrawal Request Model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    admin_charge = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # 10% charge
    net_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)    # Amount - charge
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Withdrawal"
        verbose_name_plural = "Withdrawals"
        ordering = ['-requested_date']
    
    def save(self, *args, **kwargs):
        """Calculate 10% admin charge and net amount"""
        if not self.admin_charge:
            self.admin_charge = self.amount * Decimal('0.10')  # 10% charge
            self.net_amount = self.amount - self.admin_charge
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.email} - Rs. {self.amount} ({self.status})"


class ReferralSettings(models.Model):
    """Settings for Referral Commissions"""
    direct_referral_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=200.00,
        verbose_name="Direct Referral Amount (₹)"
    )
    matching_income_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=6.00,
        verbose_name="Matching Income Percentage (%)"
    )
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Referral Settings"
        verbose_name_plural = "Referral Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one active settings instance
        if self.is_active:
            ReferralSettings.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Direct: ₹{self.direct_referral_amount}, Matching: {self.matching_income_percentage}%"


class HomePageSection(models.Model):
    """Dynamic Home Page Sections"""
    SECTION_TYPES = [
        ('hero', 'Hero Section'),
        ('features', 'Features Section'),
        ('plans', 'Income Plans'),
        ('products', 'Products Section'),
        ('testimonials', 'Testimonials'),
        ('faq', 'FAQ Section'),
    ]
    
    section_type = models.CharField(max_length=50, choices=SECTION_TYPES, unique=True)
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Home Page Section"
        verbose_name_plural = "Home Page Sections"
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.get_section_type_display()} - {self.title}"


class PlanItem(models.Model):
    """Income Plan Items for Home Page"""
    section = models.ForeignKey(HomePageSection, on_delete=models.CASCADE, related_name='plan_items', null=True, blank=True)
    icon = models.CharField(max_length=50, default='👥')
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.CharField(max_length=50, help_text="Can be percentage, amount, or symbol")
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Plan Item"
        verbose_name_plural = "Plan Items"
        ordering = ['display_order']
    
    def __str__(self):
        return self.title


class ProductItem(models.Model):
    """Product Items for Home Page"""
    section = models.ForeignKey(HomePageSection, on_delete=models.CASCADE, related_name='product_items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Prefer uploading an image; image_url kept for external images / backwards compatibility
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Home Page Product"
        verbose_name_plural = "Home Page Products"
        ordering = ['display_order']
    
    def __str__(self):
        return self.name

