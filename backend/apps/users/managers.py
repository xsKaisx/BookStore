from copy import deepcopy
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from email_validator import validate_email, EmailNotValidError
import phonenumbers as phone

class UserManager(BaseUserManager):
    def _create_user(self, username: str, login_method: str, password: str, **options):
        """
        create user on login method
        """
        if not options.get('is_active', False):
            return ValidationError('is_active must be set True')

        if login_method == 'EMAIL':
            try:
                validate_email(username)
                normalized_username = self.normalize_email(username)
                pass
            except EmailNotValidError as e:
                raise ValidationError(message='Email format is not correct. {e}')
        
        elif login_method == 'PHONENUMBER':
            parse_phone = phone.parse(username)
            if not phone.is_valid_number(parse_phone):
                raise ValidationError(message='Phone format is not correct')
            normalized_username = phone.format_in_original_format(parse_phone, phone.PhoneNumberFormat.E164)
        else:
            raise ValidationError(message='Email / Phone number is invalid')

        res = {
            **{'username': normalized_username, 'login_method': login_method},
            **options
        }
        user = self.model(**res)
        user.set_password(password)
        user.save()
        return user
    
    def create_user(self, username, login_method, password, **options):
        options_copy = deepcopy(options)
        options_copy.setdefault('is_active', True)
        options_copy.setdefault('is_staff', False)
        options_copy.setdefault('is_superuser', False)
        options_copy.setdefault('is_admin', False)

        print(f'data: {options_copy}')
        return self._create_user(username, login_method, password, **options_copy)
        
    def create_superuser(self, username, login_method, password, **options):
        options_copy = deepcopy(options)

        if login_method != 'EMAIL':
            raise ValidationError('Admin must be registered by email')
        
        options_copy.setdefault('is_active', True)
        options_copy.setdefault('is_staff', True)
        options_copy.setdefault('is_superuser', True)
        options_copy.setdefault('is_admin', True)

        print(f'data: {options_copy}')
        return self._create_user(username, login_method, password, **options_copy)