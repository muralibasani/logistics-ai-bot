"""
Insights service - generates AI-powered insights from order data.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime
from src.order_service import execute_query

logger = logging.getLogger(__name__)


def generate_insights() -> List[Dict[str, Any]]:
    """
    Generate AI insights from order data.
    
    Returns:
        List of insight dictionaries
    """
    insights = []
    
    try:
        # 1. Best Selling Products
        best_selling = get_best_selling_products()
        if best_selling:
            insights.append({
                "insight_type": "best_selling_products",
                "title": "Best Selling Products",
                "description": f"Top {len(best_selling)} products by total quantity sold",
                "data": {
                    "products": ", ".join([f"{p['product_name']} ({p['total_quantity']} units)" for p in best_selling[:5]]),
                    "top_product": best_selling[0]['product_name'] if best_selling else "N/A",
                    "total_products": str(len(best_selling))
                },
                "priority": "high"
            })
        
        # 2. Revenue Insights
        revenue_insight = get_revenue_insights()
        if revenue_insight:
            insights.append({
                "insight_type": "revenue_insights",
                "title": "Revenue Overview",
                "description": revenue_insight.get("description", "Revenue statistics"),
                "data": {
                    "total_revenue": f"${revenue_insight.get('total_revenue', 0):.2f}",
                    "average_order_value": f"${revenue_insight.get('avg_order_value', 0):.2f}",
                    "total_orders": str(revenue_insight.get('total_orders', 0))
                },
                "priority": "high"
            })
        
        # 3. Order Status Distribution
        status_dist = get_order_status_distribution()
        if status_dist:
            insights.append({
                "insight_type": "order_status_distribution",
                "title": "Order Status Overview",
                "description": "Distribution of orders by status",
                "data": status_dist,
                "priority": "medium"
            })
        
        # 4. Top Customers
        top_customers = get_top_customers()
        if top_customers:
            insights.append({
                "insight_type": "top_customers",
                "title": "Top Customers",
                "description": f"Top {len(top_customers)} customers by order value",
                "data": {
                    "customers": ", ".join([f"{c['name']} (${c['total_spent']:.2f})" for c in top_customers[:5]]),
                    "top_customer": top_customers[0]['name'] if top_customers else "N/A"
                },
                "priority": "medium"
            })
        
        # 5. Cancellation Analysis (Enhanced)
        cancellation_analysis = get_cancellation_analysis()
        if cancellation_analysis:
            # Main cancellation rate insight
            if cancellation_analysis.get('rate') is not None:
                insights.append({
                    "insight_type": "cancellation_rate",
                    "title": "Cancellation Analysis",
                    "description": f"Cancellation rate: {cancellation_analysis['rate']:.1f}%",
                    "data": {
                        "cancellation_rate": f"{cancellation_analysis['rate']:.1f}%",
                        "total_cancelled": str(cancellation_analysis['cancelled_orders']),
                        "total_orders": str(cancellation_analysis['total_orders']),
                        "top_reason": cancellation_analysis.get('top_reason', 'N/A'),
                        "recent_trend": cancellation_analysis.get('recent_trend', 'N/A')
                    },
                    "priority": "high" if cancellation_analysis['rate'] > 10 else "medium"
                })
            
            # Cancellation reasons insight
            if cancellation_analysis.get('reasons'):
                top_reasons = cancellation_analysis['reasons'][:3]
                reasons_text = ", ".join([f"{r['reason']} ({r['count']})" for r in top_reasons])
                insights.append({
                    "insight_type": "cancellation_reasons",
                    "title": "Top Cancellation Reasons",
                    "description": "Most common reasons for order cancellations",
                    "data": {
                        "top_reason": top_reasons[0]['reason'] if top_reasons else "N/A",
                        "top_reason_count": str(top_reasons[0]['count']) if top_reasons else "0",
                        "all_reasons": reasons_text,
                        "total_reasons": str(len(cancellation_analysis['reasons']))
                    },
                    "priority": "high" if cancellation_analysis['rate'] > 10 else "medium"
                })
            
            # Cancellation patterns insight
            if cancellation_analysis.get('patterns'):
                patterns = cancellation_analysis['patterns']
                insights.append({
                    "insight_type": "cancellation_patterns",
                    "title": "Cancellation Patterns",
                    "description": "Analysis of cancellation patterns and trends",
                    "data": {
                        "avg_order_value_cancelled": f"${patterns.get('avg_order_value_cancelled', 0):.2f}",
                        "avg_order_value_active": f"${patterns.get('avg_order_value_active', 0):.2f}",
                        "cancelled_by_customer": str(patterns.get('cancelled_by_customer', 0)),
                        "cancelled_by_system": str(patterns.get('cancelled_by_system', 0)),
                        "pattern_insight": patterns.get('pattern_insight', 'No significant patterns detected')
                    },
                    "priority": "medium"
                })
        
        # 6. Delivery Performance
        delivery_perf = get_delivery_performance()
        if delivery_perf:
            insights.append({
                "insight_type": "delivery_performance",
                "title": "Delivery Performance",
                "description": f"Average delivery time and success rate",
                "data": {
                    "delivered_orders": str(delivery_perf.get('delivered_count', 0)),
                    "total_orders": str(delivery_perf.get('total_orders', 0)),
                    "delivery_rate": f"{delivery_perf.get('delivery_rate', 0):.1f}%"
                },
                "priority": "medium"
            })
        
        logger.info(f"Generated {len(insights)} insights")
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        return []


def get_best_selling_products(limit: int = 10) -> List[Dict[str, Any]]:
    """Get best selling products by total quantity."""
    try:
        rows = execute_query("""
            SELECT 
                product_name,
                SUM(quantity) as total_quantity,
                SUM(quantity * price) as total_revenue,
                COUNT(DISTINCT order_id) as order_count
            FROM lg_order_items
            GROUP BY product_name
            ORDER BY total_quantity DESC
            LIMIT %s;
        """, params=(limit,))
        
        products = []
        for row in rows:
            products.append({
                "product_name": str(row[0]),
                "total_quantity": int(row[1]),
                "total_revenue": float(row[2]) if row[2] else 0.0,
                "order_count": int(row[3])
            })
        return products
    except Exception as e:
        logger.error(f"Error getting best selling products: {e}")
        return []


def get_revenue_insights() -> Dict[str, Any]:
    """Get revenue statistics."""
    try:
        rows = execute_query("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value,
                MAX(total_amount) as max_order_value,
                MIN(total_amount) as min_order_value
            FROM lg_orders
            WHERE total_amount IS NOT NULL;
        """)
        
        if not rows or not rows[0]:
            return {}
        
        row = rows[0]
        total_orders = int(row[0]) if row[0] else 0
        total_revenue = float(row[1]) if row[1] else 0.0
        avg_order_value = float(row[2]) if row[2] else 0.0
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_value": avg_order_value,
            "max_order_value": float(row[3]) if row[3] else 0.0,
            "min_order_value": float(row[4]) if row[4] else 0.0,
            "description": f"Total revenue: ${total_revenue:,.2f} from {total_orders} orders"
        }
    except Exception as e:
        logger.error(f"Error getting revenue insights: {e}")
        return {}


def get_order_status_distribution() -> Dict[str, str]:
    """Get distribution of orders by status."""
    try:
        rows = execute_query("""
            SELECT 
                order_status,
                COUNT(*) as count
            FROM lg_orders
            GROUP BY order_status
            ORDER BY count DESC;
        """)
        
        status_dict = {}
        for row in rows:
            status = str(row[0]) if row[0] else "Unknown"
            count = int(row[1])
            status_dict[status] = str(count)
        
        return status_dict
    except Exception as e:
        logger.error(f"Error getting order status distribution: {e}")
        return {}


def get_top_customers(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top customers by total order value."""
    try:
        rows = execute_query("""
            SELECT 
                c.customer_id,
                c.name,
                c.email,
                COUNT(o.order_id) as order_count,
                SUM(o.total_amount) as total_spent
            FROM lg_customers c
            INNER JOIN lg_orders o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.name, c.email
            ORDER BY total_spent DESC
            LIMIT %s;
        """, params=(limit,))
        
        customers = []
        for row in rows:
            customers.append({
                "customer_id": int(row[0]),
                "name": str(row[1]) if row[1] else "Unknown",
                "email": str(row[2]) if row[2] else "",
                "order_count": int(row[3]),
                "total_spent": float(row[4]) if row[4] else 0.0
            })
        return customers
    except Exception as e:
        logger.error(f"Error getting top customers: {e}")
        return []


def get_cancellation_analysis() -> Dict[str, Any]:
    """Get comprehensive cancellation analysis including rate, reasons, and patterns."""
    try:
        # Get basic cancellation rate
        rows = execute_query("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(DISTINCT c.order_id) as cancelled_orders
            FROM lg_orders o
            LEFT JOIN lg_order_cancellation c ON o.order_id = c.order_id;
        """)
        
        if not rows or not rows[0]:
            return {}
        
        row = rows[0]
        total_orders = int(row[0]) if row[0] else 0
        cancelled_orders = int(row[1]) if row[1] else 0
        
        if total_orders == 0:
            return {}
        
        rate = (cancelled_orders / total_orders) * 100
        
        result = {
            "total_orders": total_orders,
            "cancelled_orders": cancelled_orders,
            "rate": rate
        }
        
        # Get cancellation reasons
        reason_rows = execute_query("""
            SELECT 
                COALESCE(reason, 'Not specified') as reason,
                COUNT(*) as count
            FROM lg_order_cancellation
            GROUP BY reason
            ORDER BY count DESC
            LIMIT 10;
        """)
        
        reasons = []
        for reason_row in reason_rows:
            reasons.append({
                "reason": str(reason_row[0]) if reason_row[0] else "Not specified",
                "count": int(reason_row[1])
            })
        
        result["reasons"] = reasons
        result["top_reason"] = reasons[0]["reason"] if reasons else "N/A"
        
        # Get recent trend (cancellations in last 7 days vs previous 7 days)
        trend_rows = execute_query("""
            SELECT 
                COUNT(CASE WHEN cancel_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_cancellations,
                COUNT(CASE WHEN cancel_date >= CURRENT_DATE - INTERVAL '14 days' 
                          AND cancel_date < CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as previous_cancellations
            FROM lg_order_cancellation;
        """)
        
        if trend_rows and trend_rows[0]:
            recent = int(trend_rows[0][0]) if trend_rows[0][0] else 0
            previous = int(trend_rows[0][1]) if trend_rows[0][1] else 0
            
            if previous > 0:
                trend_change = ((recent - previous) / previous) * 100
                if trend_change > 10:
                    result["recent_trend"] = f"Increasing ({trend_change:.1f}% increase)"
                elif trend_change < -10:
                    result["recent_trend"] = f"Decreasing ({abs(trend_change):.1f}% decrease)"
                else:
                    result["recent_trend"] = "Stable"
            else:
                result["recent_trend"] = "Insufficient data"
        else:
            result["recent_trend"] = "No trend data"
        
        # Get cancellation patterns
        pattern_rows = execute_query("""
            SELECT 
                AVG(CASE WHEN c.order_id IS NOT NULL THEN o.total_amount END) as avg_cancelled_value,
                AVG(CASE WHEN c.order_id IS NULL THEN o.total_amount END) as avg_active_value,
                COUNT(CASE WHEN c.cancelled_by = 'customer' THEN 1 END) as customer_cancelled,
                COUNT(CASE WHEN c.cancelled_by = 'system' OR c.cancelled_by IS NULL THEN 1 END) as system_cancelled
            FROM lg_orders o
            LEFT JOIN lg_order_cancellation c ON o.order_id = c.order_id;
        """)
        
        patterns = {}
        if pattern_rows and pattern_rows[0]:
            row = pattern_rows[0]
            avg_cancelled = float(row[0]) if row[0] else 0.0
            avg_active = float(row[1]) if row[1] else 0.0
            customer_cancelled = int(row[2]) if row[2] else 0
            system_cancelled = int(row[3]) if row[3] else 0
            
            patterns["avg_order_value_cancelled"] = avg_cancelled
            patterns["avg_order_value_active"] = avg_active
            patterns["cancelled_by_customer"] = customer_cancelled
            patterns["cancelled_by_system"] = system_cancelled
            
            # Generate pattern insights
            pattern_insights = []
            if avg_cancelled > avg_active * 1.2:
                pattern_insights.append("Higher value orders are being cancelled more")
            elif avg_cancelled < avg_active * 0.8:
                pattern_insights.append("Lower value orders are being cancelled more")
            
            if customer_cancelled > system_cancelled * 2:
                pattern_insights.append("Most cancellations are customer-initiated")
            elif system_cancelled > customer_cancelled * 2:
                pattern_insights.append("Most cancellations are system-initiated")
            
            if not pattern_insights:
                pattern_insights.append("No significant patterns detected")
            
            patterns["pattern_insight"] = "; ".join(pattern_insights)
        
        result["patterns"] = patterns
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting cancellation analysis: {e}", exc_info=True)
        return {}


def get_delivery_performance() -> Dict[str, Any]:
    """Get delivery performance metrics."""
    try:
        rows = execute_query("""
            SELECT 
                COUNT(DISTINCT o.order_id) as total_orders,
                COUNT(DISTINCT d.order_id) as delivered_orders
            FROM lg_orders o
            LEFT JOIN lg_delivered_orders d ON o.order_id = d.order_id;
        """)
        
        if not rows or not rows[0]:
            return {}
        
        row = rows[0]
        total_orders = int(row[0]) if row[0] else 0
        delivered_orders = int(row[1]) if row[1] else 0
        
        delivery_rate = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
        
        return {
            "total_orders": total_orders,
            "delivered_count": delivered_orders,
            "delivery_rate": delivery_rate
        }
    except Exception as e:
        logger.error(f"Error getting delivery performance: {e}")
        return {}

