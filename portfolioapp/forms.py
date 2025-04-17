from django import forms
from .models import SimulationSession

class SessionForm(forms.ModelForm):
    class Meta:
        model = SimulationSession
        fields = ['amount', 'use_twitter', 'use_google', 'use_price_history']