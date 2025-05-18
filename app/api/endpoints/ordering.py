from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional
from ... import schemas, crud, models
from ...database import get_db
from ...auth.custom_auth import get_current_user, TokenData
from ...models import User, Restaurant
from fastapi import Body
from datetime import datetime
import logging
import asyncio
import json

router = APIRouter(tags=["ordering"])

# Helper function to check if user is the admin of the restaurant
async def verify_restaurant_admin(db: Session, restaurant_id: str, current_user: TokenData):
    # Check if the restaurant exists
    restaurant = db.query(Restaurant).filter(Restaurant.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail=f"Restaurant with ID {restaurant_id} not found")
    
    # Check if the current user is the restaurant admin
    if restaurant.admin_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="Only restaurant admin can perform this operation")
    
    return restaurant

# --- MENU ---
@router.get("/menu", response_model=List[schemas.MenuItemOut])
def list_menu(restaurant_id: str, db: Session = Depends(get_db)):
    return crud.get_all_menu_items(db, restaurant_id)

@router.get("/menu/categories", response_model=List[schemas.MenuCategoryOut])
def list_menu_categories(restaurant_id: str, db: Session = Depends(get_db)):
    return crud.get_all_menu_categories(db, restaurant_id)

# --- MENU CATEGORY CRUD (Admin) ---
@router.post("/menu/categories", response_model=schemas.MenuCategoryOut)
async def create_menu_category(restaurant_id: str, category: schemas.MenuCategoryCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    return crud.create_menu_category(db, restaurant_id, category)

@router.put("/menu/categories/{category_id}", response_model=schemas.MenuCategoryOut)
async def update_menu_category(category_id: int, category: schemas.MenuCategoryCreate, restaurant_id: str, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    updated = crud.update_menu_category(db, category_id, restaurant_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated

@router.delete("/menu/categories/{category_id}")
async def delete_menu_category(category_id: int, restaurant_id: str, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    deleted = crud.delete_menu_category(db, category_id, restaurant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"ok": True}

# --- MENU ITEM CRUD (Admin) ---
@router.post("/menu/items", response_model=schemas.MenuItemOut)
async def create_menu_item(restaurant_id: str, item: schemas.MenuItemCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    return crud.create_menu_item(db, restaurant_id, item)

@router.put("/menu/items/{item_id}", response_model=schemas.MenuItemOut)
async def update_menu_item(item_id: int, item: schemas.MenuItemCreate, restaurant_id: str, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    updated = crud.update_menu_item(db, item_id, restaurant_id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return updated

@router.delete("/menu/items/{item_id}")
async def delete_menu_item(item_id: int, restaurant_id: str, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    deleted = crud.delete_menu_item(db, item_id, restaurant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"ok": True}

# --- ORDERS ---

from fastapi import Security

@router.post("/order/{order_id}/confirm", response_model=schemas.OrderOut)
async def confirm_order_endpoint(
    order_id: str, 
    restaurant_id: str,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Confirm an order for a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to confirm, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    return crud.confirm_order(db, order_id, current_user.uid)

@router.post("/order/{order_id}/mark_paid", response_model=schemas.OrderOut)
async def mark_order_paid_endpoint(
    order_id: str,
    restaurant_id: str,
    payment_details: schemas.OrderMarkPaidRequest,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Mark an order as paid for a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to mark as paid, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to (for admin verification)
    - payment_details: Payment method and optional transaction ID.
    """
    # Verify admin access - this ensures the current_user is admin of this restaurant_id
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    # No need to eager load payment here, crud function will handle it.
    db_order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.restaurant_id == restaurant_id # Ensure order matches restaurant from path
    ).first()
    
    if not db_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found or does not belong to restaurant {restaurant_id}.")
    
    if db_order.payment_status == "Paid":
        # If already paid, check if customer_uid needs to be updated or if it's an error to call this again.
        # For now, the CRUD allows updating customer_uid on an already paid order. 
        # If that's not desired, this check could be more strict.
        pass # Allow proceeding to potentially update customer_uid

    try:
        updated_order = crud.mark_order_paid(
            db=db, 
            order_id=order_id, 
            changed_by=current_user.uid, 
            payment_method=payment_details.payment_method, 
            transaction_id=payment_details.transaction_id,
            customer_uid=payment_details.customer_uid # NEW: Pass customer_uid
        )
        # The updated_order from CRUD should have customer_detail loaded if customer_uid was set.
        # schemas.OrderOut is configured to handle this.
        return schemas.OrderOut.from_orm(updated_order)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logging.error(f"Error marking order {order_id} paid: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")

@router.post("/order/{order_id}/cancel", response_model=schemas.OrderOut)
async def cancel_order_endpoint(
    order_id: str,
    restaurant_id: str,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Cancel an order for a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to cancel, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    try:
        return crud.cancel_order(db, order_id, current_user.uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/order/{order_id}/refund", response_model=schemas.OrderOut)
async def refund_order_endpoint(
    order_id: str,
    restaurant_id: str,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Refund an order for a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to refund, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    try:
        return crud.refund_order(db, order_id, current_user.uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/order", response_model=schemas.OrderOut)
async def place_order(order: schemas.OrderCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    # Any authenticated user can place orders
    try:
        order_obj = None # This will store the final order (models.Order)
        # existing_unpaid_order = None # This line is not strictly needed here

        if order.table_number and order.restaurant_id:
            # Try to find an existing unpaid order for this table and restaurant
            existing_unpaid_order_model = crud.get_unpaid_order_by_table(
                db=db, 
                restaurant_id=order.restaurant_id, 
                table_number=order.table_number
            )
        else:
            existing_unpaid_order_model = None

        if existing_unpaid_order_model:
            if not order.items:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No items provided to add to existing order.")
            
            logging.info(f"Existing order {existing_unpaid_order_model.id} found for table {order.table_number}. Current items: {len(existing_unpaid_order_model.items)}, total: {existing_unpaid_order_model.total_cost}")
            logging.info(f"Attempting to add {len(order.items)} item entries.")

            # Call the modified crud function which returns the order and list of affected items
            updated_order_model, affected_item_models = crud.add_items_to_order(
                db=db,
                existing_order=existing_unpaid_order_model,
                new_items_create=order.items, # These are schemas.OrderItemCreate
                user_uid=current_user.uid
            )
            order_obj = updated_order_model

            # Convert affected model items to schema items for notification
            affected_items_schema = [schemas.OrderItemOut.from_orm(item) for item in affected_item_models]
            
            await notify_admins_items_added_to_order(order_obj.id, affected_items_schema)
            logging.info(f"Items added to order {order_obj.id}. {len(affected_items_schema)} items affected/added. New total items: {len(order_obj.items)}, new total cost: {order_obj.total_cost}")

        else:
            # No existing unpaid order, or table/restaurant not specified for check: create a new one
            order_obj = crud.create_order(
                db=db, 
                order=order, 
                user_uid=current_user.uid, 
                user_role=current_user.role
            )
            await notify_admins_new_order(order_obj.id) # Existing notification for brand new order
            logging.info(f"New order {order_obj.id} created for table {order.table_number if order.table_number else 'N/A'}.")

    except ValueError as ve:
        logging.error(f"Validation error placing order: {ve}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating/updating order or notifying admins: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to place or update order: {str(e)}")
    
    if not order_obj:
        logging.error("Order object was not created or updated successfully after all processing, returning 500.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process order.")

    # Re-fetch the order_obj with all necessary relationships for OrderOut
    # to ensure they are loaded before from_orm is called.
    db_order_for_response = db.query(models.Order).options(
        selectinload(models.Order.items).selectinload(models.OrderItem.item).selectinload(models.MenuItem.category),
        selectinload(models.Order.payment),
        selectinload(models.Order.status_history)
    ).filter(models.Order.id == order_obj.id).first()

    if not db_order_for_response:
        # This should ideally not happen if order_obj was valid
        logging.error(f"Failed to re-fetch order {order_obj.id} for response construction.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error preparing order response.")

    # Convert the final order model (whether new or updated) to the OrderOut schema for the response
    # This ensures relationships like .items and .item.category are correctly represented if loaded.
    final_order_response = schemas.OrderOut.from_orm(db_order_for_response) # Use the re-fetched object
    return final_order_response

@router.get("/orders/history", response_model=List[schemas.OrderOut])
def user_order_history(
    restaurant_id: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get order history for the current user, optionally filtered by restaurant_id.
    
    Parameters:
    - restaurant_id: Optional filter to show orders only for a specific restaurant
    """
    return crud.get_orders_by_user(db, current_user.uid, restaurant_id)

@router.get("/orders/all", response_model=List[schemas.OrderOut])
async def all_orders_history(
    restaurant_id: str,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    payment_status: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all order history for a specific restaurant, with optional filters including date range.
    Date parameters should be in ISO 8601 format (e.g., YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    """
    # Verify admin access for the restaurant
    await verify_restaurant_admin(db, restaurant_id, current_user)

    # Dates are now automatically parsed by FastAPI from ISO 8601 strings to datetime objects.
    # No manual parsing needed here.
    
    orders = crud.filter_orders(
        db=db,
        restaurant_id=restaurant_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        payment_method=None,
        user_uid=user_id,
        # The following parameters are available in crud.filter_orders but not directly in this endpoint's signature currently
        # order_id=None, 
        # user_email=None, 
        # user_phone=None
    )
    
    # The crud.filter_orders function returns a list of dictionaries that should be
    # compatible with schemas.OrderOut or be instances of models.Order that Pydantic can serialize.
    # Assuming the response_model=List[schemas.OrderOut] is on the endpoint (or will be added if not)
    return orders

@router.get("/orders/user/{user_id}", response_model=List[schemas.OrderOut])
async def orders_by_user(
    user_id: str, 
    restaurant_id: str,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get orders for a specific user, optionally filtered by restaurant_id.
    
    Parameters:
    - user_id: The user ID to get orders for
    - restaurant_id: The restaurant ID to filter orders by
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    return crud.get_orders_by_user(db, user_id, restaurant_id)

@router.get("/orders", response_model=List[schemas.OrderOut])
async def admin_list_orders(
    restaurant_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all orders for a specific restaurant.
    
    Parameters:
    - restaurant_id: Filter to show orders for this restaurant
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    return crud.get_all_orders(db, restaurant_id)

@router.get("/orders/filter", response_model=List[schemas.OrderOut])
async def filter_orders(
    restaurant_id: str,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[str] = None,
    user_id: Optional[str] = None,
    order_id: Optional[int] = None,
    user_email: Optional[str] = None,
    user_phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Filter orders by various criteria for a specific restaurant
    
    Parameters:
    - restaurant_id: The restaurant ID to filter orders by
    - status: Filter by order status
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - payment_method: Filter by payment method
    - user_id: Filter by user ID
    - order_id: Filter by order ID
    - user_email: Filter by user email (partial match)
    - user_phone: Filter by user phone (partial match)
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # Parse dates if provided
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    return crud.filter_orders(
        db,
        status=status,
        start_date=start,
        end_date=end,
        payment_method=payment_method,
        user_id=user_id,
        order_id=order_id,
        user_email=user_email,
        user_phone=user_phone,
        restaurant_id=restaurant_id
    )

@router.put("/order/{order_id}/status", response_model=schemas.OrderOut)
async def update_order_status(
    order_id: str, 
    restaurant_id: str,
    status: str = Body(...), 
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update the status of an order for a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to update, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    - status: The new status for the order
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    try:
        return crud.update_order_status(db, order_id, status, current_user.uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- PAYMENT ---

@router.get("/order/{order_id}/receipt")
async def order_receipt(
    order_id: str,
    restaurant_id: str,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get the receipt for an order from a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to get the receipt for, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    """
    # Verify admin access or if user owns the order
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()

    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )

    # Check if current user is admin or the user who placed the order
    is_admin = False
    try:
        await verify_restaurant_admin(db, restaurant_id, current_user) # This will raise HTTPException if not admin
        is_admin = True
    except HTTPException as admin_check_failed:
        if db_order.user_uid != current_user.uid:
            raise HTTPException(status_code=403, detail="You do not have permission to view this receipt.") from admin_check_failed
    
    # Allow receipt generation if conditions were previously less strict, adjust as needed
    # if db_order.status not in ["Completed", "Done"] and db_order.payment_status not in ["Paid", "Refunded"]:
    #     raise HTTPException(status_code=400, detail="Receipt only available for completed or paid orders.")
    
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io
    
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "Order Receipt")
    p.setFont("Helvetica", 12)
    p.drawString(50, 720, f"Order ID: {db_order.id}")
    p.drawString(50, 700, f"User ID: {db_order.user_uid}") # Changed from user_id
    p.drawString(50, 680, f"Restaurant ID: {db_order.restaurant_id}") # Use db_order.restaurant_id
    if db_order.table_number:
        p.drawString(50, 660, f"Table Number: {db_order.table_number}")
        p.drawString(50, 640, f"Created At: {utc_to_ist(db_order.created_at).strftime('%Y-%m-%d %I:%M %p') if db_order.created_at else 'N/A'}")
        p.drawString(50, 620, f"Status: {db_order.status}")
        p.drawString(50, 600, f"Payment Status: {db_order.payment_status}")
        y_start_items = 570
    else:
        p.drawString(50, 660, f"Created At: {utc_to_ist(db_order.created_at).strftime('%Y-%m-%d %I:%M %p') if db_order.created_at else 'N/A'}")
        p.drawString(50, 640, f"Status: {db_order.status}")
        p.drawString(50, 620, f"Payment Status: {db_order.payment_status}")
        y_start_items = 590

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_start_items, "Items:")
    y = y_start_items - 20
    p.setFont("Helvetica", 12)
    for item in db_order.items:
        p.drawString(60, y, f"{item.quantity} x {item.item.name} @ {item.price} each")
        y -= 18
    p.drawString(50, y-10, f"Total: {db_order.total_cost}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=receipt_order_{order_id}.pdf"})


@router.get("/order/{order_id}/audit")
async def order_audit_log(
    order_id: str,
    restaurant_id: str,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get the audit log for an order from a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to get the audit log for, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    logs = db.query(models.AuditLog).filter(models.AuditLog.order_id == order_id).order_by(models.AuditLog.timestamp.desc()).all()
    
    # Return as dicts for readability
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp
        }
        for log in logs
    ]

@router.put("/order/{order_id}/payment", response_model=schemas.PaymentOut)
async def update_payment_status(
    order_id: str,
    restaurant_id: str,
    payment: schemas.PaymentCreate, 
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update payment status for an order from a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to update payment for, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    - payment: Payment details
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(models.Order).options(
        joinedload(models.Order.items).joinedload(models.OrderItem.item)
    ).filter(models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    try:
        return crud.update_payment(db, order_id, payment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- PROMO CODE ---
@router.post("/promo/apply", response_model=schemas.PromoCodeOut)
def apply_promo_code(code: str = Body(...), db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    return crud.apply_promo_code(db, code, current_user.uid)

# --- PROMO CODE CRUD (Admin) ---
@router.post("/promo", response_model=schemas.PromoCodeOut)
def create_promo_code(promo: schemas.PromoCodeCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    return crud.create_promo_code(db, promo)

@router.get("/promo", response_model=List[schemas.PromoCodeOut])
def list_promo_codes(db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    return crud.get_all_promo_codes(db)

@router.put("/promo/{promo_id}", response_model=schemas.PromoCodeOut)
def update_promo_code(promo_id: int, promo: schemas.PromoCodeCreate, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    updated = crud.update_promo_code(db, promo_id, promo)
    if not updated:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return updated

@router.delete("/promo/{promo_id}")
def delete_promo_code(promo_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    deleted = crud.delete_promo_code(db, promo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return {"ok": True}

# --- ANALYTICS ---
@router.get("/analytics/orders", response_model=dict)
async def order_analytics(
    restaurant_id: str,
    period: Optional[str] = "daily", 
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get order analytics for a specific restaurant
    
    Parameters:
    - restaurant_id: The restaurant ID to get analytics for
    - period: Time period for analytics (daily, weekly, monthly)
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    return crud.get_order_analytics(db, period=period)

from fastapi.responses import StreamingResponse
import io

@router.get("/orders/export")
async def export_orders(
    restaurant_id: str,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    payment_method: Optional[str] = None,
    user_id: Optional[str] = None,
    order_id: Optional[int] = None,
    user_email: Optional[str] = None,
    user_phone: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Export orders to CSV with optional filters for a specific restaurant
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    orders = crud.filter_orders(
        db,
        status=status,
        start_date=start,
        end_date=end,
        payment_method=payment_method,
        user_id=user_id,
        order_id=order_id,
        user_email=user_email,
        user_phone=user_phone,
        restaurant_id=restaurant_id
    )
    
    csv_data = crud.export_orders_csv(db, orders)
    return StreamingResponse(io.StringIO(csv_data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=orders.csv"})

# --- REAL-TIME NOTIFICATIONS (WebSocket) ---

# Use a dict to map websocket to its asyncio.Queue
active_admin_connections = {}

@router.websocket("/ws/admin/orders")
async def admin_orders_ws(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue()
    active_admin_connections[websocket] = queue
    # Background task to send notifications
    async def sender():
        try:
            while True:
                notification = await queue.get()
                await websocket.send_text(json.dumps(notification))
        except Exception as e:
            logging.exception(f"WebSocket sender task exception: {e}")
    sender_task = asyncio.create_task(sender())
    try:
        while True:
            # Only wait for client pings/keepalives
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        sender_task.cancel()
        del active_admin_connections[websocket]

async def notify_admins_new_order(order_id: int):
    print(f"[KDS_DEBUG] notify_admins_new_order called for order_id: {order_id}")
    # Put a notification on every connected admin's queue
    for queue in list(active_admin_connections.values()):
        try:
            await queue.put({"event": "new_order", "order_id": order_id})
        except Exception as e:
            logging.exception(f"Failed to queue new order notification: {e}")

async def notify_admins_items_added_to_order(order_id: str, affected_items: List[schemas.OrderItemOut]):
    print(f"[KDS_DEBUG] notify_admins_items_added_to_order called for order_id: {order_id}")
    affected_items_data = []
    for item_out in affected_items:
        if item_out.item: 
            affected_items_data.append({
                "item_name": item_out.item.name,
                "quantity": item_out.quantity,
                "price": item_out.price,
                "item_id": item_out.item.id
            })
        else:
            affected_items_data.append({
                "item_name": "Unknown Item (Data not fully loaded)",
                "quantity": item_out.quantity,
                "price": item_out.price,
            })
    print(f"[KDS_DEBUG] Affected items for order {order_id}: {affected_items_data}")
    # Put a notification on every connected admin's queue for items added
    for queue in list(active_admin_connections.values()):
        try:
            await queue.put({
                "type": "items_added_to_order", 
                "order_id": order_id, 
                "affected_items": affected_items_data
            })
        except Exception as e:
            logging.exception(f"Failed to queue items_added notification for order {order_id} to websocket {queue}: {e}")
