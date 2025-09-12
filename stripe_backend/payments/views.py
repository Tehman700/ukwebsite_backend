from rest_framework.decorators import api_view
from rest_framework.response import Response
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
def create_checkout_session(request):
    data = request.data
    products = data.get("products", [])

    line_items = [
        {
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": item["item_name"]},
                "unit_amount": int(item["price"] * 100),
            },
            "quantity": item["quantity"],
        }
        for item in products
    ]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url="http://localhost:3000/#success",
        cancel_url="http://localhost:3000/#cancel",
    )

    return Response({"id": session.id})
