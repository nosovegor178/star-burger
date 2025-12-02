from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.templatetags.static import static
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import IntegerField,\
    ModelSerializer, Serializer, DecimalField

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


class OrderItemSerializer(Serializer):
    product = IntegerField(min_value=1)
    quantity = IntegerField(min_value=1)


class OrderSerializer(ModelSerializer):
    id = IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ['id',
                  'firstname',
                  'lastname',
                  'phonenumber',
                  'address']


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    response = request.data
    serializer = OrderSerializer(data=response)
    serializer.is_valid(raise_exception=True)
    order = serializer.save()
    for product_item in response['products']:
        order_serializer = OrderItemSerializer(data=product_item)
        order_serializer.is_valid(raise_exception=True)
        product = Product.objects.get(id=product_item['product'])
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=product_item['quantity'],
            price=product.price
        )
    return Response(serializer.data)
