from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas
import logging

logger = logging.getLogger(__name__)

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
    return db_table

def get_table(db: Session, table_id: int, restaurant_id: str) -> Optional[models.RestaurantTable]:
  
    return db.query(models.RestaurantTable).filter(
        models.RestaurantTable.id == table_id,
        models.RestaurantTable.restaurant_id == restaurant_id
    ).first()

def get_table_by_number(db: Session, table_number: str, restaurant_id: str) -> Optional[models.RestaurantTable]:
   
    return db.query(models.RestaurantTable).filter(
        models.RestaurantTable.table_number == table_number,
        models.RestaurantTable.restaurant_id == restaurant_id
    ).first()

def list_tables_by_restaurant(db: Session, restaurant_id: str, skip: int = 0, limit: int = 100) -> List[models.RestaurantTable]:

    return db.query(models.RestaurantTable).filter(
        models.RestaurantTable.restaurant_id == restaurant_id
    ).order_by(models.RestaurantTable.table_number.asc()).offset(skip).limit(limit).all()

def update_table_details(db: Session, table_id: int, restaurant_id: str, update_data: schemas.RestaurantTableUpdate) -> Optional[models.RestaurantTable]:
 
    db_table = get_table(db, table_id, restaurant_id)
    if not db_table:
        return None

    update_values = update_data.dict(exclude_unset=True)
    
    # If table_number is being updated, check for uniqueness
    if 'table_number' in update_values and update_values['table_number'] != db_table.table_number:
        existing_table = get_table_by_number(db, table_number=update_values['table_number'], restaurant_id=restaurant_id)
        if existing_table:
            raise ValueError(f"Table number {update_values['table_number']} already exists for restaurant {restaurant_id}.")

    for key, value in update_values.items():
        setattr(db_table, key, value)
    
    db.commit()
    db.refresh(db_table)
    return db_table

def delete_restaurant_table(db: Session, table_id: int, restaurant_id: str) -> bool:
  
    db_table = get_table(db, table_id, restaurant_id)
    if not db_table:
        return False
    
    db.delete(db_table)
    db.commit()
    return True 