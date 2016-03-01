import logging
from django import forms
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from analysis_service.base import models


logger = logging.getLogger("django")


class PublicKeyFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        super(PublicKeyFileField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        uploaded_file = super(PublicKeyFileField, self).clean(data, initial)
        if uploaded_file.size > 100000:
            raise ValidationError(
                'File size must be at most 100kB, actual size is {}'.format(
                    filesizeformat(uploaded_file.size)
                )
            )
        contents = uploaded_file.read()
        if not contents.startswith('ssh-rsa AAAAB3'):
            raise ValidationError(
                'Invalid public key (a public key should start with \'ssh-rsa AAAAB3\')'
            )
        return contents


class NewClusterForm(forms.ModelForm):
    identifier = forms.RegexField(
        required=True,
        regex="^[\w-]{1,100}$",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[\w-]+',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'A brief description of the cluster\'s purpose, '
                            'visible in the AWS management console.',
            'data-validation-pattern-message': 'Valid names are strings of alphanumeric '
                                               'characters, \'_\', and \'-\'.',
        })
    )
    size = forms.IntegerField(
        required=True,
        min_value=1, max_value=20,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'required': 'required',
            'min': '1', 'max': '20',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'Number of workers to use in the cluster '
                            '(1 is recommended for testing or development).',
        })
    )
    public_key = PublicKeyFileField(
        required=True,
        widget=forms.FileInput(attrs={'required': 'required'})
    )

    def save(self, user):
        # create the model without committing, since we haven't
        # set the required created_by field yet
        new_cluster = super(NewClusterForm, self).save(commit=False)

        # set the field to the user that created the cluster
        new_cluster.created_by = models.User.objects.get(email=user.email)

        # the new model is complete, so now we can save it
        return new_cluster.save()

    class Meta:
        model = models.Cluster
        fields = ['identifier', 'size', 'public_key']


class NewWorkerForm(forms.ModelForm):
    identifier = forms.RegexField(
        required=True,
        regex="^[\w-]{1,100}$",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '[\w-]+',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'A brief description of the cluster\'s purpose, '
                            'visible in the AWS management console.',
            'data-validation-pattern-message': 'Valid names are strings of alphanumeric '
                                               'characters, \'_\', and \'-\'.',
        })
    )
    public_key = PublicKeyFileField(
        required=True,
        widget=forms.FileInput(attrs={'required': 'required'})
    )

    def save(self, user):
        # create the model without committing, since we haven't
        # set the required created_by field yet
        new_cluster = super(NewWorkerForm, self).save(commit=False)

        # set the field to the user that created the cluster
        new_cluster.created_by.queryset = models.User.objects.filter(email=user.email)

        # the new model is complete, so now we can save it
        return new_cluster.save()

    class Meta:
        model = models.Cluster
        fields = ['identifier', 'public_key']
