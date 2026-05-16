import os, json, time
from typing import Optional

class StripeClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("STRIPE_API_KEY", "")

    def create_payment_intent(self, amount_cents: int, currency: str = "usd",
                              metadata: dict = None) -> dict:
        if not self.api_key:
            return {"error": "Stripe not configured"}
        import stripe
        stripe.api_key = self.api_key
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata or {},
            automatic_payment_methods={"enabled": True},
        )
        return {"id": intent.id, "client_secret": intent.client_secret,
                "amount": intent.amount, "status": intent.status}

    def confirm_payment(self, payment_intent_id: str) -> dict:
        if not self.api_key:
            return {"error": "Stripe not configured"}
        import stripe
        stripe.api_key = self.api_key
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {"id": intent.id, "status": intent.status, "paid": intent.status == "succeeded"}
