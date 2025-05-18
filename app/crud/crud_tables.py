from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Tuple

from .. import models, schemas
from app.utils.text_utils import slugify
import logging

logger = logging.getLogger(__name__)

def _generate_composed_table_id(db: Session, restaurant_id: str, table_number: str) -> Optional[str]:
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id).first()
    if restaurant:
        return f"{slugify(restaurant.restaurant_name)}-{table_number}"
    return None

def _parse_table_number_from_composed_id(composed_id: str, restaurant_slug: str) -> Optional[str]:
    """Extracts table_number from composed_id, assuming format restaurant_slug-table_number."""
    if composed_id.startswith(restaurant_slug + '-'):
        return composed_id[len(restaurant_slug) + 1:]
    return None # Or raise error if format is unexpected

def create_restaurant_table(db: Session, restaurant_id: str, table_data: schemas.RestaurantTableCreate) -> models.RestaurantTable:
   
    # Ensure table_number is unique for this restaurant before creating
    existing_table = db.query(models.RestaurantTable).filter(
        models.RestaurantTable.restaurant_id == restaurant_id,
        models.RestaurantTable.table_number == table_data.table_number
    ).first()
    if existing_table:
        raise ValueError(f"Table number {table_data.table_number} already exists for restaurant {restaurant_id}.")

    db_table = models.RestaurantTable(
        **table_data.dict(),
        restaurant_id=restaurant_id
    )
    db.add(db_table)
    db.commit()
    db.refresh(db_table)
    # Dynamically add composed_table_id for the response schema
    db_table.composed_table_id = _generate_composed_table_id(db, db_table.restaurant_id, db_table.table_number)
    return db_table

def get_table(db: Session, table_id: int, restaurant_id: str) -> Optional[models.RestaurantTable]:
  
    db_table = db.query(models.RestaurantTable).options(joinedload(models.RestaurantTable.restaurant)).filter(
        models.RestaurantTable.id == table_id,
        models.RestaurantTable.restaurant_id == restaurant_id
    ).first()
    if db_table:
        db_table.composed_table_id = _generate_composed_table_id(db, db_table.restaurant_id, db_table.table_number)
    return db_table

def get_table_by_number(db: Session, table_number: str, restaurant_id: str) -> Optional[models.RestaurantTable]:
   
    db_table = db.query(models.RestaurantTable).options(joinedload(models.RestaurantTable.restaurant)).filter(
        models.RestaurantTable.table_number == table_number,
        models.RestaurantTable.restaurant_id == restaurant_id
    ).first()
    if db_table:
        db_table.composed_table_id = _generate_composed_table_id(db, db_table.restaurant_id, db_table.table_number)
    return db_table

def get_table_by_composed_id(db: Session, composed_id: str, restaurant_id_from_path: str) -> Optional[models.RestaurantTable]:
    """Fetches a table using its composed ID and the restaurant_id from the path."""
    restaurant = db.query(models.Restaurant).filter(models.Restaurant.restaurant_id == restaurant_id_from_path).first()
    if not restaurant:
        # This case should ideally be caught by verify_restaurant_admin in the endpoint
        logger.warning(f"Restaurant not found for ID: {restaurant_id_from_path} while trying to get table by composed_id: {composed_id}")
        return None
    
    expected_slug = slugify(restaurant.restaurant_name)
    table_number = _parse_table_number_from_composed_id(composed_id, expected_slug)

    if not table_number:
        logger.warning(f"Could not parse table_number from composed_id '{composed_id}' for restaurant slug '{expected_slug}'.")
        return None # Or raise a specific error indicating malformed composed_id
        
    return get_table_by_number(db, table_number=table_number, restaurant_id=restaurant_id_from_path)

def list_tables_by_restaurant(db: Session, restaurant_id: str, skip: int = 0, limit: int = 100) -> List[models.RestaurantTable]:

    tables = db.query(models.RestaurantTable).options(joinedload(models.RestaurantTable.restaurant)).filter(
        models.RestaurantTable.restaurant_id == restaurant_id
    ).order_by(models.RestaurantTable.table_number.asc()).offset(skip).limit(limit).all()
    for table in tables:
        table.composed_table_id = _generate_composed_table_id(db, table.restaurant_id, table.table_number)
    return tables

def update_table_details(db: Session, composed_id: str, restaurant_id: str, update_data: schemas.RestaurantTableUpdate) -> Optional[models.RestaurantTable]:
 
    db_table = get_table_by_composed_id(db, composed_id=composed_id, restaurant_id_from_path=restaurant_id)
    if not db_table:
        return None

    update_values = update_data.dict(exclude_unset=True)
    
    if 'table_number' in update_values and update_values['table_number'] != db_table.table_number:
        existing_table_with_new_number = get_table_by_number(db, table_number=update_values['table_number'], restaurant_id=restaurant_id)
        if existing_table_with_new_number and existing_table_with_new_number.id != db_table.id:
            raise ValueError(f"Table number {update_values['table_number']} already exists for restaurant {restaurant_id}.")

    for key, value in update_values.items():
        setattr(db_table, key, value)
    
    db.commit()
    db.refresh(db_table)
    db_table.composed_table_id = _generate_composed_table_id(db, db_table.restaurant_id, db_table.table_number)
    return db_table

def delete_restaurant_table(db: Session, composed_id: str, restaurant_id: str) -> bool:
  
    db_table = get_table_by_composed_id(db, composed_id=composed_id, restaurant_id_from_path=restaurant_id)
    if not db_table:
        return False
    
    db.delete(db_table)
    db.commit()
    return True 