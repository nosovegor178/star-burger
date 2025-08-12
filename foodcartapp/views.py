from django.db.models import Max
from django.http import JsonResponse
from django.templatetags.static import static
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer


import json


from .models import Product, Order, OrderItem



def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderItemSerializer(ModelSerializer):
    product = PrimaryKeyRelatedField(queryset=Product.objects.all())
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        max_id = Product.objects.aggregate(Max('id'))['id__max']
        extra_kwargs = {
            'quantity': {'min_value': 1},
            'product': {'min_value': 1, 'max_value': max_id}
        }

class OrderSerializer(ModelSerializer):
    products = OrderItemSerializer(many=True)
    phonenumber = PhoneNumberField()
    
    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'phonenumber', 'address', 'products']


@api_view(['POST'])
def register_order(request):
    response = request.data
    serializer = OrderSerializer(data=response)
    serializer.is_valid(raise_exception=True)

    order = Order.objects.create(
        firstname=response['firstname'],
        lastname=response['lastname'],
        phonenumber=response['phonenumber'],
        adress=response['address'],)
    for product in response['products']:
        OrderItem.objects.create(
            order=order,
            product=Product.objects.get(id=product['product']),
            quantity=product['quantity']
        )
    return Response(response)
