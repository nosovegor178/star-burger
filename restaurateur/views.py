from django import forms
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from geopy import distance
import requests

from addresses.models import Address
from foodcartapp.models import Product, Restaurant, Order


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


def fetch_coordinates(apikey, address):
    try:
        try:
            address = Address.objects.get(address=address)
            lon = address.lon
            lat = address.lat
        except ObjectDoesNotExist:
            base_url = "https://geocode-maps.yandex.ru/1.x"
            response = requests.get(base_url, params={
                "geocode": address,
                "apikey": apikey,
                "format": "json",
            })
            response.raise_for_status()
            found_places = response.json()['response']['GeoObjectCollection']\
                ['featureMember']

            if not found_places:
                return None

            most_relevant = found_places[0]
            lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

            Address.objects.create(
                address=address,
                lon=lon,
                lat=lat
            )
        return lat, lon
    except requests.HTTPError:
        return None


def fetch_orders_with_distance_to_restaurants(orders):
    for order in orders:
        address_coords = fetch_coordinates(settings.YANDEX_API_KEY,
                                           order.address)
        restaurants = order.ready_restaurants
        if not address_coords:
            for i, restaurant in enumerate(restaurants):
                restaurants[i] += ', ошибка определения координат'
            order.ready_restaurants = restaurants
        else:
            for i, restaurant in enumerate(restaurants):
                restaurant_coords = fetch_coordinates(settings.YANDEX_API_KEY,
                                                      restaurant)
                if not restaurant_coords:
                    restaurants[i] += ', ошибка определения координат'
                else:
                    restaurants[i] += ', {} км'.format(
                        distance.distance(restaurant_coords,
                                          address_coords).km
                    )
            order.ready_restaurants = sorted(restaurants)
    return orders


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    return render(request, template_name='order_items.html', context={
        'orders': fetch_orders_with_distance_to_restaurants(
            Order.objects.returns_order_price().returns_ready_restaurants()
            )
    })
