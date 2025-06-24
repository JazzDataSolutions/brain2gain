from decimal import Decimal
from typing import Any, Dict


class ShippingService:
    """Service responsible for shipping cost calculations."""

    async def calculate_shipping_cost(
        self, subtotal: Decimal, shipping_address: Dict[str, Any]
    ) -> Decimal:
        """Calculate shipping cost based on subtotal and address."""
        if subtotal >= Decimal("1000"):
            return Decimal(0)

        base_shipping = Decimal("150")
        state = shipping_address.get("state", "").upper()
        if state in {"CDMX", "MEXICO", "GUADALAJARA"}:
            return base_shipping
        return base_shipping * Decimal("1.5")
