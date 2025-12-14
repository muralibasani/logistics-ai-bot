"""
FastAPI endpoints for order operations.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from src.order_service import get_order_count, get_order_status, get_order_details, cancel_order, refund_order
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Order Management API")


class OrderStatusResponse(BaseModel):
    order_id: int
    exists: bool
    status: Optional[str] = None
    total_amount: Optional[float] = None
    has_cancellation: bool = False
    has_refund: bool = False


class OrderCountResponse(BaseModel):
    total_orders: int
    by_status: dict


class CancelOrderResponse(BaseModel):
    success: bool
    message: str
    order_id: int


class RefundOrderResponse(BaseModel):
    success: bool
    message: str
    order_id: int
    refund_amount: Optional[float] = None


class OrderItem(BaseModel):
    product_name: Optional[str] = None
    quantity: int = 0
    price: float = 0.0


class OrderTracking(BaseModel):
    status: Optional[str] = None
    location: Optional[str] = None
    timestamp: Optional[str] = None


class CancellationInfo(BaseModel):
    cancel_date: Optional[str] = None
    reason: Optional[str] = None
    cancelled_by: Optional[str] = None


class RefundInfo(BaseModel):
    refund_date: Optional[str] = None
    refund_amount: Optional[float] = None
    refund_status: Optional[str] = None


class DeliveryInfo(BaseModel):
    delivered_date: Optional[str] = None
    delivery_person: Optional[str] = None
    comments: Optional[str] = None


class OrderDetailsResponse(BaseModel):
    order_id: int
    exists: bool
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    order_date: Optional[str] = None
    order_status: Optional[str] = None
    total_amount: Optional[float] = None
    items: List[OrderItem] = []
    tracking: List[OrderTracking] = []
    cancellation: Optional[CancellationInfo] = None
    refund: Optional[RefundInfo] = None
    delivery: Optional[DeliveryInfo] = None


@app.get("/orders/count", response_model=OrderCountResponse)
async def get_order_count_endpoint():
    """Get the total count of orders and count by status."""
    try:
        result = get_order_count()
        return OrderCountResponse(**result)
    except Exception as e:
        logger.error(f"Error getting order count: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting order count: {str(e)}")


@app.get("/orders/{order_id}/status", response_model=OrderStatusResponse)
async def get_order_status_endpoint(order_id: int):
    """Get the status and details of a specific order."""
    try:
        result = get_order_status(order_id)
        if not result.get("exists"):
            return OrderStatusResponse(
                order_id=order_id,
                exists=False
            )
        return OrderStatusResponse(**result)
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting order status: {str(e)}")


@app.get("/orders/{order_id}/details", response_model=OrderDetailsResponse)
async def get_order_details_endpoint(order_id: int):
    """Get comprehensive details of a specific order including customer, items, tracking, cancellation, refund, and delivery information."""
    try:
        result = get_order_details(order_id)
        if not result.get("exists"):
            return OrderDetailsResponse(
                order_id=order_id,
                exists=False
            )
        return OrderDetailsResponse(**result)
    except Exception as e:
        logger.error(f"Error getting order details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting order details: {str(e)}")


@app.post("/orders/{order_id}/cancel", response_model=CancelOrderResponse)
async def cancel_order_endpoint(order_id: int):
    """Cancel an order by updating its status and creating a cancellation record."""
    try:
        result = cancel_order(order_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return CancelOrderResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")


@app.post("/orders/{order_id}/refund", response_model=RefundOrderResponse)
async def refund_order_endpoint(order_id: int):
    """Refund an order by updating its status and creating a refund record."""
    try:
        result = refund_order(order_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))
        return RefundOrderResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refunding order: {e}")
        raise HTTPException(status_code=500, detail=f"Error refunding order: {str(e)}")

