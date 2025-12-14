"""
Order service layer - business logic for order operations.
"""
import os
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Parse database URI and create connection
def get_db_connection():
    """Get a PostgreSQL database connection."""
    db_uri = os.getenv("DB_URI")
    if not db_uri:
        raise ValueError("DB_URI environment variable is not set")
    
    # Parse the URI
    parsed = urlparse(db_uri)
    
    # Extract connection parameters
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password
    }
    
    # Remove None values
    conn_params = {k: v for k, v in conn_params.items() if v is not None}
    
    return psycopg2.connect(**conn_params)


def execute_query(query: str, params: Optional[Tuple] = None, fetch: bool = True) -> List[Tuple]:
    """
    Execute a SQL query and return results.
    
    Args:
        query: SQL query string
        params: Optional tuple of parameters for parameterized queries
        fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE/DELETE)
    
    Returns:
        List of tuples representing rows
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()
                return []
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing query: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()



def get_order_count() -> Dict:
    """Get the total count of orders and count by status."""
    try:
        # Get total count
        total_rows = execute_query("SELECT COUNT(*) FROM lg_orders;")
        total_count = int(total_rows[0][0]) if total_rows else 0

        # Get count by status
        status_rows = execute_query("""
            SELECT order_status, COUNT(*)
            FROM lg_orders
            GROUP BY order_status;
        """)

        by_status = {
            str(status): int(count)
            for status, count in status_rows
        }

        return {
            "total_orders": total_count,
            "by_status": by_status
        }

    except Exception as e:
        logger.error("Error getting order count", exc_info=True)
        raise


def get_order_status(order_id: int) -> Dict:
    """Get the status and details of a specific order."""
    try:
        rows = execute_query("""
            SELECT
                o.order_id,
                o.order_status,
                o.total_amount,
                c.cancel_id IS NOT NULL AS has_cancellation,
                r.refund_id IS NOT NULL AS has_refund
            FROM lg_orders o
            LEFT JOIN lg_order_cancellation c ON o.order_id = c.order_id
            LEFT JOIN lg_refunds r ON o.order_id = r.order_id
            WHERE o.order_id = %s;
        """, params=(order_id,))

        if not rows:
            return {
                "order_id": order_id,
                "exists": False
            }

        order_id_val, status, total, has_cancel, has_refund = rows[0]

        return {
            "order_id": int(order_id_val),
            "exists": True,
            "status": str(status),
            "total_amount": float(total) if total is not None else None,
            "has_cancellation": bool(has_cancel),
            "has_refund": bool(has_refund),
        }
    except Exception as e:
        logger.error(f"Error getting order status: {e}", exc_info=True)
        raise


def get_order_details(order_id: int) -> Dict:
    """Get comprehensive details of a specific order including customer, items, tracking, cancellation, refund, and delivery information."""
    try:
        # Get order basic info with customer details
        order_rows = execute_query("""
            SELECT
                o.order_id,
                o.customer_id,
                o.order_date,
                o.order_status,
                o.total_amount,
                c.name AS customer_name,
                c.email AS customer_email,
                c.phone AS customer_phone
            FROM lg_orders o
            LEFT JOIN lg_customers c ON o.customer_id = c.customer_id
            WHERE o.order_id = %s;
        """, params=(order_id,))

        if not order_rows:
            return {
                "order_id": order_id,
                "exists": False
            }

        order_row = order_rows[0]
        order_id_val, customer_id, order_date, order_status, total_amount, customer_name, customer_email, customer_phone = order_row

        # Get order items
        items_rows = execute_query("""
            SELECT product_name, quantity, price
            FROM lg_order_items
            WHERE order_id = %s
            ORDER BY item_id;
        """, params=(order_id,))

        items = []
        for item_row in items_rows:
            product_name, quantity, price = item_row
            items.append({
                "product_name": str(product_name) if product_name else None,
                "quantity": int(quantity) if quantity else 0,
                "price": float(price) if price else 0.0
            })

        # Get tracking information
        tracking_rows = execute_query("""
            SELECT status, location, timestamp
            FROM lg_order_tracking
            WHERE order_id = %s
            ORDER BY timestamp;
        """, params=(order_id,))

        tracking = []
        for track_row in tracking_rows:
            status, location, timestamp = track_row
            tracking.append({
                "status": str(status) if status else None,
                "location": str(location) if location else None,
                "timestamp": timestamp.isoformat() if timestamp else None
            })

        # Get cancellation info
        cancel_rows = execute_query("""
            SELECT cancel_date, reason, cancelled_by
            FROM lg_order_cancellation
            WHERE order_id = %s;
        """, params=(order_id,))

        cancellation = None
        if cancel_rows:
            cancel_date, reason, cancelled_by = cancel_rows[0]
            cancellation = {
                "cancel_date": cancel_date.isoformat() if cancel_date else None,
                "reason": str(reason) if reason else None,
                "cancelled_by": str(cancelled_by) if cancelled_by else None
            }

        # Get refund info
        refund_rows = execute_query("""
            SELECT refund_date, refund_amount, refund_status
            FROM lg_refunds
            WHERE order_id = %s;
        """, params=(order_id,))

        refund = None
        if refund_rows:
            refund_date, refund_amount, refund_status = refund_rows[0]
            refund = {
                "refund_date": refund_date.isoformat() if refund_date else None,
                "refund_amount": float(refund_amount) if refund_amount else None,
                "refund_status": str(refund_status) if refund_status else None
            }

        # Get delivery info
        delivery_rows = execute_query("""
            SELECT delivered_date, delivery_person, comments
            FROM lg_delivered_orders
            WHERE order_id = %s;
        """, params=(order_id,))

        delivery = None
        if delivery_rows:
            delivered_date, delivery_person, comments = delivery_rows[0]
            delivery = {
                "delivered_date": delivered_date.isoformat() if delivered_date else None,
                "delivery_person": str(delivery_person) if delivery_person else None,
                "comments": str(comments) if comments else None
            }

        return {
            "order_id": int(order_id_val),
            "exists": True,
            "customer_id": int(customer_id) if customer_id else None,
            "customer_name": str(customer_name) if customer_name else None,
            "customer_email": str(customer_email) if customer_email else None,
            "customer_phone": str(customer_phone) if customer_phone else None,
            "order_date": order_date.isoformat() if order_date else None,
            "order_status": str(order_status) if order_status else None,
            "total_amount": float(total_amount) if total_amount else None,
            "items": items,
            "tracking": tracking,
            "cancellation": cancellation,
            "refund": refund,
            "delivery": delivery
        }
    except Exception as e:
        logger.error(f"Error getting order details: {e}", exc_info=True)
        raise


def cancel_order(order_id: int) -> Dict:
    """Cancel an order by updating its status and creating a cancellation record."""
    try:
        # First check if order exists and can be cancelled
        status = get_order_status(order_id)
        
        if not status.get("exists"):
            return {
                "success": False,
                "message": f"Order {order_id} does not exist",
                "order_id": order_id
            }
        
        if status.get("has_cancellation") or status.get("has_refund") or status.get("status") in ['Cancelled', 'Refunded']:
            return {
                "success": False,
                "message": f"Order {order_id} cannot be cancelled. It is already cancelled or refunded.",
                "order_id": order_id
            }
        
        # Execute cancellation
        # 1. Update order status
        execute_query(
            "UPDATE lg_orders SET order_status = 'Cancelled' WHERE order_id = %s;",
            params=(order_id,),
            fetch=False
        )
        
        # 2. Insert cancellation record
        execute_query(
            "INSERT INTO lg_order_cancellation (order_id, reason, cancelled_by) VALUES (%s, %s, %s);",
            params=(order_id, 'Customer request', 'system'),
            fetch=False
        )
        
        return {
            "success": True,
            "message": f"Order {order_id} has been successfully cancelled",
            "order_id": order_id
        }
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        return {
            "success": False,
            "message": f"Error cancelling order: {str(e)}",
            "order_id": order_id
        }


def refund_order(order_id: int) -> Dict:
    """Refund an order by updating its status and creating a refund record."""
    try:
        # First check if order exists and can be refunded
        status = get_order_status(order_id)
        
        if not status.get("exists"):
            return {
                "success": False,
                "message": f"Order {order_id} does not exist",
                "order_id": order_id,
                "refund_amount": None
            }
        
        if status.get("has_cancellation") or status.get("has_refund") or status.get("status") in ['Cancelled', 'Refunded']:
            return {
                "success": False,
                "message": f"Order {order_id} cannot be refunded. It is already cancelled or refunded.",
                "order_id": order_id,
                "refund_amount": None
            }
        
        total_amount = status.get("total_amount")
        
        # Execute refund
        # 1. Update order status
        execute_query(
            "UPDATE lg_orders SET order_status = 'Refunded' WHERE order_id = %s;",
            params=(order_id,),
            fetch=False
        )
        
        # 2. Insert refund record
        if total_amount is not None:
            execute_query(
                "INSERT INTO lg_refunds (order_id, refund_amount, refund_status) VALUES (%s, %s, %s);",
                params=(order_id, total_amount, 'Completed'),
                fetch=False
            )
        else:
            execute_query(
                "INSERT INTO lg_refunds (order_id, refund_amount, refund_status) VALUES (%s, (SELECT total_amount FROM lg_orders WHERE order_id = %s), %s);",
                params=(order_id, order_id, 'Completed'),
                fetch=False
            )
        
        return {
            "success": True,
            "message": f"Order {order_id} has been successfully refunded",
            "order_id": order_id,
            "refund_amount": total_amount
        }
    except Exception as e:
        logger.error(f"Error refunding order: {e}")
        return {
            "success": False,
            "message": f"Error refunding order: {str(e)}",
            "order_id": order_id,
            "refund_amount": None
        }

