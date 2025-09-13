from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.conf import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
@api_view(['POST', 'OPTIONS'])
def create_checkout_session(request):
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return Response({}, status=status.HTTP_200_OK)

    try:
        data = request.data
        products = data.get("products", [])

        # Validate that products exist
        if not products:
            return Response(
                {"error": "No products provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build line items with validation
        line_items = []
        for item in products:
            # Validate required fields
            if not all(key in item for key in ['item_name', 'price', 'quantity']):
                return Response(
                    {"error": "Missing required fields in product data"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate price is positive
            if item['price'] <= 0:
                return Response(
                    {"error": f"Invalid price for item {item['item_name']}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            line_items.append({
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": item["item_name"],
                        "description": item.get("description", "")  # Optional description
                    },
                    "unit_amount": int(item["price"] * 100),  # Convert to pence
                },
                "quantity": int(item["quantity"]),
            })

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="http://18.212.225.123/#success",
            cancel_url="http://18.212.225.123/#cancel",
            # Optional: Add metadata for tracking
            metadata={
                'integration_check': 'accept_a_payment',
                'order_items': len(products)
            }
        )

        logger.info(f"Checkout session created: {session.id}")
        return Response({"id": session.id}, status=status.HTTP_200_OK)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return Response(
            {"error": "Payment processing error. Please try again."},
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:
        logger.error(f"Unexpected error in create_checkout_session: {str(e)}")
        return Response(
            {"error": "An unexpected error occurred. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )