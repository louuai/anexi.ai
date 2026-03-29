CUSTOMER_VIEW_PRODUCT = "customer_view_product"
CUSTOMER_ADD_TO_CART = "customer_add_to_cart"
CUSTOMER_CHECKOUT_START = "customer_checkout_start"
CUSTOMER_PURCHASE = "customer_purchase"
ORDER_CANCELLED = "order_cancelled"
ORDER_REFUNDED = "order_refunded"
CALL_CONFIRMED = "call_confirmed"
CALL_FAILED = "call_failed"

VALID_EVENT_TYPES = {
    CUSTOMER_VIEW_PRODUCT,
    CUSTOMER_ADD_TO_CART,
    CUSTOMER_CHECKOUT_START,
    CUSTOMER_PURCHASE,
    ORDER_CANCELLED,
    ORDER_REFUNDED,
    CALL_CONFIRMED,
    CALL_FAILED,
}

EVENT_TYPE_ALIASES = {
    "product_view": CUSTOMER_VIEW_PRODUCT,
    "view_product": CUSTOMER_VIEW_PRODUCT,
    "add_to_cart": CUSTOMER_ADD_TO_CART,
    "checkout_start": CUSTOMER_CHECKOUT_START,
    "purchase": CUSTOMER_PURCHASE,
    "order_created": CUSTOMER_PURCHASE,
    "order_cancel": ORDER_CANCELLED,
    "refund_created": ORDER_REFUNDED,
    "call_ok": CALL_CONFIRMED,
    "call_confirm": CALL_CONFIRMED,
    "call_nok": CALL_FAILED,
}

