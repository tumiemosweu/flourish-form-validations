from django import forms
from django.apps import apps as django_apps
from edc_action_item.site_action_items import site_action_items
from edc_constants.constants import NO, NEW
from flourish_prn.action_items import CAREGIVEROFF_STUDY_ACTION


class FormValidatorMixin:

    consent_version_model = 'flourish_caregiver.flourishconsentversion'
    caregiver_offstudy_model = 'flourish_prn.caregiveroffstudy'
    subject_consent_model = 'flourish_caregiver.subjectconsent'

    @property
    def consent_version_cls(self):
        return django_apps.get_model(self.consent_version_model)

    @property
    def caregiver_offstudy_cls(self):
        return django_apps.get_model(self.caregiver_offstudy_model)

    @property
    def subject_consent_cls(self):
        return django_apps.get_model(self.subject_consent_model)

    def clean(self):
        if self.cleaned_data.get('maternal_visit'):
            self.subject_identifier = self.cleaned_data.get(
                'maternal_visit').subject_identifier
            self.validate_against_visit_datetime(
                self.cleaned_data.get('report_datetime'))
        else:
            self.subject_identifier = self.cleaned_data.get('subject_identifier')

        self.validate_consent_version_obj()
        super().clean()

    def validate_against_consent_datetime(self, report_datetime):
        """Returns an instance of the current maternal consent or
        raises an exception if not found."""

        if self.latest_consent_obj:
            if report_datetime and report_datetime < self.latest_consent_obj.consent_datetime:
                raise forms.ValidationError(
                    "Report datetime cannot be before consent datetime")
        else:
            raise forms.ValidationError(
                    'Please complete Caregiver Consent form '
                    f'before proceeding.')

    def validate_against_visit_datetime(self, report_datetime):
        if (report_datetime and report_datetime <
                self.cleaned_data.get('maternal_visit').report_datetime):
            raise forms.ValidationError(
                "Report datetime cannot be before visit datetime.")

    def validate_offstudy_model(self):

        action_cls = site_action_items.get(
            self.caregiver_offstudy_cls.action_name)
        action_item_model_cls = action_cls.action_item_model_cls()

        try:
            action_item_model_cls.objects.get(
                subject_identifier=self.subject_identifier,
                action_type__name=CAREGIVEROFF_STUDY_ACTION,
                status=NEW)
        except action_item_model_cls.DoesNotExist:
            try:
                self.caregiver_offstudy_cls.objects.get(
                    subject_identifier=self.subject_identifier)
            except self.caregiver_offstudy_cls.DoesNotExist:
                pass
            else:
                raise forms.ValidationError(
                    'Participant has been taken offstudy. Cannot capture any '
                    'new data.')
        else:
            self.maternal_visit = self.cleaned_data.get('maternal_visit') or None
            if not self.maternal_visit or self.maternal_visit.require_crfs == NO:
                raise forms.ValidationError(
                    'Participant is scheduled to be taken offstudy without '
                    'any new data collection. Cannot capture any new data.')

    def validate_consent_version_obj(self):

        if self.latest_consent_obj:
            try:
                self.consent_version_cls.objects.get(
                    screening_identifier=self.latest_consent_obj.screening_identifier)
            except self.consent_version_cls.DoesNotExist:
                raise forms.ValidationError(
                    'Consent version form has not been completed, kindly complete it before'
                    ' continuing.')

    @property
    def latest_consent_obj(self):

        subject_consents = self.subject_consent_cls.objects.filter(
            subject_identifier=self.subject_identifier)

        if subject_consents:
            return subject_consents.latest('consent_datetime')
