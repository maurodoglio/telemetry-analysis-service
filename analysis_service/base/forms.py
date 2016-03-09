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
            'pattern': r'[\w-]+',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'A brief description of the cluster\'s purpose, '
                            'visible in the AWS management console.',
            'data-validation-pattern-message': 'Valid cluster names are strings of alphanumeric '
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

        # actually start the real cluster, and return the model object
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
            'pattern': r'[\w-]+',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'A brief description of the worker\'s purpose, '
                            'visible in the AWS management console.',
            'data-validation-pattern-message': 'Valid worker names are strings of alphanumeric '
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
        new_worker = super(NewWorkerForm, self).save(commit=False)

        # set the field to the user that created the worker
        new_worker.created_by = models.User.objects.get(email=user.email)

        # actually start the real worker, and return the model object
        return new_worker.save()

    class Meta:
        model = models.Worker
        fields = ['identifier', 'public_key']


class NewScheduledSparkForm(forms.ModelForm):
    identifier = forms.RegexField(
        required=True,
        regex="^[\w-]{1,100}$",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': r'[\w-]+',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'A brief description of the scheduled Spark job\'s purpose, '
                            'visible in the AWS management console.',
            'data-validation-pattern-message': 'Valid job names are strings of alphanumeric '
                                               'characters, \'_\', and \'-\'.',
        })
    )
    notebook = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'required': 'required'})
    )
    result_visibility = forms.ChoiceField(
        choices=[
            ('private', 'Private: results output to an S3 bucket, viewable with AWS credentials'),
            ('public', 'Public: results output to a public S3 bucket, viewable by anyone'),
        ],
        widget=forms.Select(
            attrs={'class': 'form-control', 'required': 'required'}
        )
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
            'data-content': 'Number of workers to use when running the Spark job '
                            '(1 is recommended for testing or development).',
        })
    )
    interval_in_hours = forms.ChoiceField(
        choices=[
            (24, "Daily"),
            (24 * 7, "Weekly"),
            (24 * 30, "Monthly"),
        ],
        widget=forms.Select(
            attrs={'class': 'form-control', 'required': 'required'}
        )
    )
    job_timeout = forms.IntegerField(
        required=True,
        min_value=1, max_value=24,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'required': 'required',
            'min': '1', 'max': '24',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'Number of hours that a single run of the job can run '
                            'for before timing out and being terminated.',
        })
    )
    start_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control datetimepicker',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'Date/time on which to enable the scheduled Spark job.',
        })
    )
    end_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control datetimepicker',
            'data-toggle': 'popover',
            'data-trigger': 'focus',
            'data-placement': 'top',
            'data-container': 'body',
            'data-content': 'Date/time on which to disable the scheduled Spark job '
                            '- leave this blank if the job should not be disabled.',
        })
    )

    def save(self, user):
        # create the model without committing, since we haven't
        # set the required created_by field yet
        new_scheduled_spark = super(NewScheduledSparkForm, self).save(commit=False)

        # set the field to the user that created the scheduled Spark job
        new_scheduled_spark.created_by = models.User.objects.get(email=user.email)

        # actually save the scheduled Spark job, and return the model object
        return new_scheduled_spark.save()

    class Meta:
        model = models.ScheduledSpark
        fields = ['identifier', 'size', 'interval_in_hours', 'start_date', 'end_date']
