from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import uuid
import imghdr

from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    receipt_image_url = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Expense
        fields = [
            'id', 'user', 'user_username', 'receipt_image', 'receipt_image_url',
            'date', 'category', 'custom_category', 'category_display', 'amount', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_receipt_image_url(self, obj):
        if obj.receipt_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt_image.url)
        return None
    
    def get_category_display(self, obj):
        return obj.get_category_display_name()

class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            'receipt_image', 'date', 'category', 'custom_category',
            'amount', 'description'
        ]
    
    def validate(self, data):
        # If category is 'Others', custom_category is required
        if data.get('category') == 'Others' and not data.get('custom_category'):
            raise serializers.ValidationError({
                'custom_category': 'This field is required when category is "Others".'
            })
        
        # If category is not 'Others', clear custom_category
        if data.get('category') != 'Others':
            data['custom_category'] = ''
        
        return data

    def create(self, validated_data):
        """Handle receipt image provided as base64 string or uploaded file.

        The view calls `serializer.save(user=request.user)` so `user` may be
        present in validated_data (DRF merges kwargs into validated_data).
        """
        user = validated_data.pop('user', None)

        receipt = validated_data.get('receipt_image')
        if receipt and isinstance(receipt, str):
            # Expecting data URI format: data:<mime>;base64,<data>
            if receipt.startswith('data:') and ';base64,' in receipt:
                header, imgstr = receipt.split(';base64,')
                # Try to get extension from header
                try:
                    ext = header.split('/')[-1]
                except Exception:
                    ext = 'png'
                file_name = f"receipt_{uuid.uuid4().hex[:8]}.{ext}"
                try:
                    decoded = base64.b64decode(imgstr)
                except Exception:
                    raise serializers.ValidationError({'receipt_image': 'Invalid base64 image data.'})

                # If ext is generic, try to detect image type
                if ext in ('octet-stream', ''):
                    detected = imghdr.what(None, h=decoded)
                    if detected:
                        ext = detected
                        file_name = f"receipt_{uuid.uuid4().hex[:8]}.{ext}"

                validated_data['receipt_image'] = ContentFile(decoded, name=file_name)

        # Create the expense with optional user
        if user:
            expense = Expense.objects.create(user=user, **validated_data)
        else:
            expense = Expense.objects.create(**validated_data)

        return expense