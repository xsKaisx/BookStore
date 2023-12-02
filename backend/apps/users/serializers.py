from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q

import re
import traceback
import phonenumbers
import json
from rest_framework import serializers, exceptions

from . import models
from lib.common import book_lib
from lib.common.book_lib import log

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length = 255)
    password = serializers.CharField(max_length = 255)
    confirm_password = serializers.CharField(max_length = 255)
    phone_region_code = serializers.CharField(max_length=3, allow_null=True, allow_blank=True, default=None)
    login_method = serializers.ChoiceField(choices = models.LOGIN_METHOD)
    first_name = serializers.CharField(allow_null=True, allow_blank=True, default=None)
    last_name = serializers.CharField(allow_null=True, allow_blank=True, default=None)

    def validate(self, data):
        if re.findall('\s', data['username']):
            raise exceptions.ValidationError('Email/Phone number can not contain any space')

        # check if user exist
        try:
            user: models.User = models.User.objects.filter(Q(username = data['username'])).count()
            if user:
                log.error(f'User {user.id} already exists')
                raise exceptions.ValidationError(detail = "User already exists")
        except Exception as e:
            raise e
        
        if data['login_method'] == 'EMAIL':
            try:
                validate_email(data['username'])
            except Exception as e:
                raise exceptions.ValidationError(detail=str(e))
        if data['login_method'] == 'PHONENUMBER':
            try:
                parsed_phone = phonenumbers.parse(data['username'], data['phone_region_code'])
            except phonenumbers.NumberParseException:
                raise exceptions.ValidationError(f"Invalid phone number")
        
        name_pat = '^[A-Z][a-zA-Z\s]+'
        if (data['first_name'] is None or data['first_name'] ==''):
            data['first_name']=None
        elif (not bool(re.match(name_pat, data['first_name']))):
            raise exceptions.ValidationError(detail = 'first_name must start with a capital letter and does not contain any special characters')
        if (data['last_name'] is None or data['last_name'] ==''):
            data['last_name']=None
        elif (not bool(re.match(name_pat, data['last_name']))):
            raise exceptions.ValidationError(detail = 'last_name must start with a capital letter and does not contain any special characters')

        # validate passwords match
        if not (data['confirm_password'] == data['password']):
            raise exceptions.ValidationError(detail = 'passwords are not matched')

        # validate password
        if not book_lib.validate_password_strong(data['password']):
            raise exceptions.ValidationError(detail = 'password is not strong')

        log.info('_______before return data in validation ________')
        log.info('\n' + json.dumps(data, indent=4) + '\n')
        return data        

    def create_user(self, validated_data) -> tuple[models.User, models.UserProfile]:
        log.info('___________validated_data___________')
        log.info(validated_data)
        try:
            create_data = {**validated_data}
            del create_data['phone_region_code']
            del create_data['confirm_password']

            with transaction.atomic():
                user = models.User.objects.create_user(
                    username=create_data['username'],
                    login_method=create_data['login_method'],
                    password=create_data['password']
                )
                if validated_data['login_method'] == 'EMAIL':
                    profile = models.UserProfile.objects.create(
                        user = user,
                        first_name = validated_data['first_name'],
                        last_name = validated_data['last_name'],
                        email = validated_data['username'],
                    )

                if validated_data['login_method'] == 'PHONENUMBER':
                    profile = models.UserProfile.objects.create(
                        user = user,
                        first_name = validated_data['first_name'],
                        last_name = validated_data['last_name'],
                        phone = validated_data['username'],
                    )
            return user, profile
        except Exception as e:
            tb = traceback.format_exc()
            log.error(f'Hitting exception ({e}) while trying to create user. {tb}')
            raise exceptions.ErrorDetail(f"Could not create user from serializer {self.__class__.__name__}")
        
class LoginSerializer(serializers.Serializer):
    username = serializers.EmailField(max_length = 255)
    password = serializers.CharField(max_length = 255)
    login_method = serializers.ChoiceField(choices = models.LOGIN_METHOD, default = 'EMAIL')

    def validate(self, data):
        acceptable_login_methods = [login_choice[0] for login_choice in models.LOGIN_METHOD]
        if data['login_method'] not in acceptable_login_methods:
            raise exceptions.ValidationError(detail = f'Invalid login method. Only accept one of these values {acceptable_login_methods}')
        return data     

class UserModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        exclude = ['password']

class UserProfileModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserProfile
        fields ='__all__'