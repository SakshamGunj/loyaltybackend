# This __init__.py file makes app/crud a package.
# It exposes functions from modules *within* this 'crud' directory.

# Import from general CRUD functions
from .general import (
    create_user, get_user, get_user_by_email, get_user_by_number, update_user, delete_user,
    disassociate_employee_from_restaurant,
    slugify, generate_coupon_code, # Added generate_coupon_code assuming it's in general.py
    create_restaurant, get_restaurant, get_restaurants,
    create_loyalty, get_loyalty, list_loyalties,
    create_submission, get_submission, list_submissions,
    create_claimed_reward, get_claimed_reward, list_claimed_rewards,
    create_audit_log, list_audit_logs,
    get_all_menu_categories, create_menu_category, get_menu_category, update_menu_category, delete_menu_category,
    get_all_menu_items, create_menu_item, get_menu_item, update_menu_item, delete_menu_item,
    create_order, get_orders_by_user, get_all_orders, filter_orders, update_order_status,
    confirm_order, mark_order_paid, cancel_order, refund_order,
    update_payment,
    apply_promo_code, create_promo_code, get_all_promo_codes, update_promo_code, delete_promo_code,
    get_order_analytics, export_orders_csv,
    get_unpaid_order_by_table, add_items_to_order
)

# Import from inventory-specific CRUD functions
from .crud_inventory import (
    # _create_inventory_log_entry, # Usually internal, expose if explicitly needed
    get_inventory_item,
    get_inventory_item_by_menu_id,
    create_inventory_item,
    update_inventory_item_stock,
    list_inventory_update_logs,
    deduct_inventory_for_sale
)

# Import from coupon-specific CRUD functions
from .crud_coupons import (
    create_coupon_instance,
    get_coupon_by_id,
    get_coupon_by_code,
    list_coupons,
    update_coupon,
    deactivate_coupon,
    record_coupon_usage,
    get_coupon_total_usage_count,
    get_user_coupon_usage_count
)

# Import from table-specific CRUD functions
from .crud_tables import (
    create_restaurant_table,
    get_table,
    get_table_by_number,
    list_tables_by_restaurant,
    update_table_details,
    delete_restaurant_table
)

# If you have other specific CRUD files (e.g., app/crud/crud_coupons.py), import from them similarly:
# from .crud_coupons import (
#    create_coupon,
#    get_coupon,
#    # etc.
# )


# Define __all__ for explicit export control if needed for 'from app.crud import *'
__all__ = [
    # Functions from .general
    "create_user", "get_user", "get_user_by_email", "get_user_by_number", "update_user", "delete_user",
    "disassociate_employee_from_restaurant",
    "slugify", "generate_coupon_code",
    "create_restaurant", "get_restaurant", "get_restaurants",
    "create_loyalty", "get_loyalty", "list_loyalties",
    "create_submission", "get_submission", "list_submissions",
    "create_claimed_reward", "get_claimed_reward", "list_claimed_rewards",
    "create_audit_log", "list_audit_logs",
    "get_all_menu_categories", "create_menu_category", "get_menu_category", "update_menu_category", "delete_menu_category",
    "get_all_menu_items", "create_menu_item", "get_menu_item", "update_menu_item", "delete_menu_item",
    "create_order", "get_orders_by_user", "get_all_orders", "filter_orders", "update_order_status",
    "confirm_order", "mark_order_paid", "cancel_order", "refund_order",
    "update_payment",
    "apply_promo_code", "create_promo_code", "get_all_promo_codes", "update_promo_code", "delete_promo_code",
    "get_order_analytics", "export_orders_csv",
    "get_unpaid_order_by_table", "add_items_to_order",

    # Functions from .crud_inventory
    "get_inventory_item", "get_inventory_item_by_menu_id", "create_inventory_item",
    "update_inventory_item_stock", "list_inventory_update_logs", "deduct_inventory_for_sale",

    # Functions from .crud_coupons
    "create_coupon_instance",
    "get_coupon_by_id",
    "get_coupon_by_code",
    "list_coupons",
    "update_coupon",
    "deactivate_coupon",
    "record_coupon_usage",
    "get_coupon_total_usage_count",
    "get_user_coupon_usage_count",

    # Functions from .crud_tables
    "create_restaurant_table",
    "get_table",
    "get_table_by_number",
    "list_tables_by_restaurant",
    "update_table_details",
    "delete_restaurant_table",

    # Add functions from other crud files like crud_coupons to this list as well if they exist
]

# Note: Functions in app/crud.py (the file, i.e., parent_directory.crud)
# should be imported directly by consumers, e.g.:
# from app import crud as app_crud_module (to access app/crud.py)
# then app_crud_module.create_user()
#
# Or, more commonly, if 'from app import crud' in an endpoint refers to app/crud.py,
# then that endpoint will use crud.create_user(), etc. directly from app/crud.py.
#
# This __init__.py avoids re-exporting from app/crud.py to prevent circular dependencies
# that arise when the app.crud package (this __init__.py) is being initialized. 