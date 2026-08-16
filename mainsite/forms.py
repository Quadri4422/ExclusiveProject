from django import forms
from .models import Order

INPUT_CLASSES = "w-full bg-[#F5F5F5] rounded border-none px-4 py-3.5 text-sm text-black focus:outline-none focus:ring-2 focus:ring-[#DB4444]"

class CheckoutForm(forms.ModelForm):
    save_info = forms.BooleanField(required=False, initial=True)

    class Meta:
        model = Order
        fields = [
            'first_name', 'company_name', 'street_address', 
            'apartment', 'city', 'phone', 'email', 'payment_method'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'id': 'first_name'}),
            'company_name': forms.TextInput(attrs={'class': INPUT_CLASSES, 'id': 'company_name'}),
            'street_address': forms.TextInput(attrs={'class': INPUT_CLASSES, 'id': 'street_address'}),
            'apartment': forms.TextInput(attrs={'class': INPUT_CLASSES, 'id': 'apartment'}),
            'city': forms.TextInput(attrs={'class': INPUT_CLASSES, 'id': 'city'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'class': INPUT_CLASSES, 'id': 'phone'}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES, 'id': 'email'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'accent-black cursor-pointer'}),
        }