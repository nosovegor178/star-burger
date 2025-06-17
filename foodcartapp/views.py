from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


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


@api_view(['POST'])
def register_order(request):
    # TODO это лишь заглушка
    response = request.data
    order = Order.objects.create(
        firstname=response['firstname'],
        lastname=response['lastname'],
        phonenumber=response['phonenumber'],
        adress=response['address'],
    )
    try:
        if not response['products']:
            return Response({'products': 'Это поле не может быть пустым'},
                            status=status.HTTP_404_NOT_FOUND)
        if not isinstance(response['products'], list):
            return Response({'products': 'Ожидался list со значениями'},
                            status=status.HTTP_404_NOT_FOUND)
        if response['products']==[]:
            return Response({'products': 'Этот список не может быть пустым'},
                            status=status.HTTP_404_NOT_FOUND)
    except KeyError:
        return Response({'products': 'Обязательное поле'},
                            status=status.HTTP_404_NOT_FOUND)
    for product in response['products']:
        OrderItem.objects.create(
            order=order,
            product=Product.objects.get(id=product['product']),
            quantity=product['quantity']
        )
    return Response(response)
