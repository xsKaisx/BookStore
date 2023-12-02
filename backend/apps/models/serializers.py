from rest_framework import serializers, exceptions
from . import models

class BookModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Book
        fields = '__all__'

class UpdateBookModelSerializer(serializers.Serializer):
    book_id = serializers.CharField(max_length=255)
    author = serializers.CharField(max_length=255, required=False)
    title = serializers.CharField(max_length=255, required=False)
    book_cover = serializers.ImageField(required=False)
    publish_date = serializers.DateField(required=False)
    isbn = serializers.CharField(max_length=255, required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    available = serializers.BooleanField(default=True, required=False)

    def validate(self, data):
        if data.get('isbn'):
            book = models.Book.objects.get(isbn = data['isbn'])
            if book:
                raise exceptions.ValidationError('Invalid isbn')
        if data.get('price'):
            if data.get('price') <= 0:
                raise exceptions.ValidationError('Price can not lower than 0')
        return data
    
class DeleteBookModelSerializer(serializers.Serializer):
    book_id = serializers.CharField(max_length=255)

    def validate(self, data):
        try:
            book = models.Book.objects.get(pk = data['book_id'])
        except:  
            raise exceptions.ValidationError('Invalid book_id')
        return data