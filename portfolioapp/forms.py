from django import forms
from .models import SimulationSession, Stock


class SessionForm(forms.ModelForm):
    stocks = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = SimulationSession
        fields = ["amount", "use_twitter", "use_google", "use_price_history", "stocks"]

    def clean_stocks(self):
        data = self.cleaned_data["stocks"]
        symbols = [s.strip().upper() for s in data.split(",") if s.strip()]
        return symbols  # return list of symbols for now
