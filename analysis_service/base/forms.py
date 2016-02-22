from django import forms


class NewClusterForm(forms.Form):
    identifier = forms.CharField(required=True, widget=forms.TextInput(attrs={
        "class": "form-control",
        "data-toggle": "popover",
        "data-trigger": "focus",
        "data-placement": "top",
        "data-container": "body",
        "data-content": "A brief description of the cluster's purpose, visible in the AWS management console.",
    }))
    size = forms.IntegerField(required=True, min_value=1, widget=forms.TextInput(attrs={
        "class": "form-control",
        "data-toggle": "popover",
        "data-trigger": "focus",
        "data-placement": "top",
        "data-container": "body",
        "data-content": "Number of workers to use in the cluster (1 is recommended for testing or development).",
    }))
    public_key = forms.FileField(required=True)
