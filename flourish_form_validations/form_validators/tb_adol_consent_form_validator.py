from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.conf import settings
from edc_constants.constants import NO
from edc_form_validators import FormValidatorMixin, FormValidator


class TbAdolConsentFormValidator(FormValidator, FormValidatorMixin):
    
    
    subject_consent_model = 'flourish_caregiver.subjectconsent'
    
    @property
    def subject_consent_cls(self):
        return django_apps.get_model(self.subject_consent_model)

    def clean(self):
        super().clean()
        self.consent_validation()
        
        
        
    def consent_validation(self):
        
        # used to get the consent from flourish
        subject_identifier = self.cleaned_data.get('subject_identifier', None)
        
            
        # fields to be validated if there are the same
            
        fields = [
            'first_name',
            'last_name',
            'initials',
            'is_literate',
            'dob',
            'is_dob_estimated',
            'citizen',
            'identity',
            'confirm_identity',
            
        ]
        
        # To avoid errors when running tests because there is an additional model being 
        # used from flourish caregiver
        

        
        try:
            flourish_subject_consent = self.subject_consent_cls.objects.filter(
                subject_identifier = subject_identifier
            ).last()
            
        except self.subject_consent_cls.DoesNotExist:
            raise ValidationError("Flourish Consent Doesn't exist")
        else:
            
            
            for field in fields:
                flourish_consent_value = flourish_subject_consent.__dict__.get(field, None)
                tb_consent_values = self.cleaned_data.get(field, None)
                
                if not flourish_subject_consent:
                    raise ValidationError({field: "Value specified in does not exist in flourish consent, please fill it"})
                
                if not tb_consent_values:
                    raise ValidationError({field: "Please fill the value"})
                
                if tb_consent_values != flourish_consent_value:
                    raise ValidationError({
                        field : "TB Consent value not the same as the flourish consent"
                    })
                    
                    
            
            

            
