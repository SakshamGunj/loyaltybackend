from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from ... import schemas, crud
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
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
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
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Mark an order as paid for a specific restaurant.
    
    Parameters:
    - order_id: The ID of the order to mark as paid, in format "restaurant_id_number"
    - restaurant_id: The restaurant ID the order belongs to
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    try:
        return crud.mark_order_paid(db, order_id, current_user.uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
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
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
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
    order_obj = crud.create_order(db, order, current_user.uid)
    # Notify admins (await directly)
    try:
        await notify_admins_new_order(order_obj.id)
    except Exception as e:
        logging.exception(f"Error notifying admins for new order: {e}")
    return order_obj

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

@router.get("/orders/all")
async def all_orders_history(
    restaurant_id: str,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None, 
    payment_status: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all orders filtered by restaurant_id and optional parameters
    
    Parameters:
    - restaurant_id: The restaurant ID to filter orders by (required)
    - status: Filter by order status
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - payment_status: Filter by payment status
    - user_id: Filter by customer user ID
    """
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    # Parse dates if provided
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    # We'll reuse the filter_orders function but with restaurant_id being required
    return crud.filter_orders(
        db,
        restaurant_id=restaurant_id,
        status=status,
        start_date=start,
        end_date=end,
        payment_status=payment_status,
        user_id=user_id
    )

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
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
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
    # Verify admin access
    await verify_restaurant_admin(db, restaurant_id, current_user)
    
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io
    
    # First, verify the order exists and belongs to the specified restaurant
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    if db_order.status not in ["Completed", "Done"] and db_order.payment_status not in ["Paid", "Refunded"]:
        raise HTTPException(status_code=400, detail="Receipt only available for completed or paid orders.")
    
    # Generate PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "Order Receipt")
    p.setFont("Helvetica", 12)
    p.drawString(50, 720, f"Order ID: {db_order.id}")
    p.drawString(50, 700, f"User ID: {db_order.user_id}")
    p.drawString(50, 680, f"Restaurant ID: {restaurant_id}")
    p.drawString(50, 660, f"Created At: {db_order.created_at}")
    p.drawString(50, 640, f"Status: {db_order.status}")
    p.drawString(50, 620, f"Payment Status: {db_order.payment_status}")
    y = 590
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Items:")
    y -= 20
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
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    # Check if the order belongs to the specified restaurant
    if db_order.restaurant_id != restaurant_id:
        raise HTTPException(
            status_code=403, 
            detail="This order does not belong to the specified restaurant."
        )
    
    logs = db.query(crud.models.AuditLog).filter(crud.models.AuditLog.order_id == order_id).order_by(crud.models.AuditLog.timestamp.desc()).all()
    
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
    db_order = db.query(crud.models.Order).options(
        joinedload(crud.models.Order.items).joinedload(crud.models.OrderItem.item)
    ).filter(crud.models.Order.id == order_id).first()
    
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
    # Put a notification on every connected admin's queue
    for queue in list(active_admin_connections.values()):
        try:
            await queue.put({"event": "new_order", "order_id": order_id})
        except Exception as e:
            logging.exception(f"Failed to queue new order notification: {e}")
