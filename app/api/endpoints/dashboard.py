from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from typing import List, Dict, Any, Optional
import logging

router = APIRouter(prefix="/api/userdashboard", tags=["userdashboard"])

# Set up logger
logger = logging.getLogger(__name__)

@router.get("/")
def user_dashboard(uid: str, db: Session = Depends(get_db)):
    """
    Get user dashboard data with fault-tolerant handling of potential missing data.
    """
    try:
        # Collect base data
        loyalties = crud.list_loyalties(db, uid=uid)
        submissions = crud.list_submissions(db, uid=uid)
        claimed_rewards = crud.list_claimed_rewards(db, uid=uid)
        audit_logs = crud.list_audit_logs(db, uid=uid)

        # Organize claimed rewards by restaurant
        rewards_by_restaurant = {}
        for reward in claimed_rewards:
            if not hasattr(reward, 'restaurant_id') or not reward.restaurant_id:
                logger.warning(f"Missing restaurant_id for reward {getattr(reward, 'id', 'unknown')}")
                continue
            rid = reward.restaurant_id
            if rid not in rewards_by_restaurant:
                rewards_by_restaurant[rid] = []
            rewards_by_restaurant[rid].append(reward)

        # Organize submissions by restaurant for spend
        spend_by_restaurant = {}
        for sub in submissions:
            try:
                if not hasattr(sub, 'restaurant_id') or not sub.restaurant_id:
                    logger.warning(f"Missing restaurant_id for submission {getattr(sub, 'submission_id', 'unknown')}")
                    continue
                rid = sub.restaurant_id
                amount_spent = getattr(sub, 'amount_spent', 0) or 0
                spend_by_restaurant[rid] = spend_by_restaurant.get(rid, 0) + amount_spent
            except Exception as e:
                logger.warning(f"Error processing submission: {e}")
                continue

        dashboard = []
        # Get unique restaurant IDs from both sources
        restaurant_ids = set(list(rewards_by_restaurant.keys()) + list(spend_by_restaurant.keys()))
        
        for rid in restaurant_ids:
            try:
                restaurant = crud.get_restaurant(db, rid)
                if not restaurant:
                    logger.warning(f"Restaurant not found for ID: {rid}")
                    continue
                
                # Get reward thresholds with safety checks
                reward_thresholds = []
                try:
                    if hasattr(restaurant, 'reward_thresholds') and restaurant.reward_thresholds:
                        if isinstance(restaurant.reward_thresholds, list):
                            reward_thresholds = sorted(restaurant.reward_thresholds, key=lambda x: x.get('points', 0) if isinstance(x, dict) else 0)
                except Exception as e:
                    logger.warning(f"Error processing reward thresholds for restaurant {rid}: {e}")
                
                # Get spend thresholds with safety checks
                spend_thresholds = []
                try:
                    if hasattr(restaurant, 'spend_thresholds') and restaurant.spend_thresholds:
                        if isinstance(restaurant.spend_thresholds, list):
                            spend_thresholds = sorted(restaurant.spend_thresholds, key=lambda x: x.get('amount', 0) if isinstance(x, dict) else 0)
                except Exception as e:
                    logger.warning(f"Error processing spend thresholds for restaurant {rid}: {e}")
                
                # Spin stats with safety checks
                points_per_spin = getattr(restaurant, 'points_per_spin', 1) or 1
                num_spins = len(rewards_by_restaurant.get(rid, []))
                current_spin_points = num_spins * points_per_spin
                
                # Calculate which spin rewards are met
                spin_rewards_met = []
                upcoming_spin_rewards = []
                
                try:
                    for th in reward_thresholds:
                        # Use get with default value to safely access dict keys
                        threshold = th.get('points', 0) if isinstance(th, dict) else 0
                        reward_name = th.get('reward', '') if isinstance(th, dict) else ''
                        
                        if not reward_name:  # Skip if reward name is empty
                            continue
                        
                        # Find claimed reward for this threshold
                        claimed = None
                        try:
                            if rid in rewards_by_restaurant:
                                for cr in rewards_by_restaurant[rid]:
                                    if (hasattr(cr, 'reward_name') and cr.reward_name == reward_name and 
                                        current_spin_points >= threshold):
                                        claimed = cr
                                        break
                        except Exception as e:
                            logger.warning(f"Error finding claimed reward: {e}")
                            
                        if current_spin_points >= threshold:
                            coupon_code = getattr(claimed, 'coupon_code', None) if claimed else None
                            spin_rewards_met.append({
                                "threshold": threshold, 
                                "reward": reward_name, 
                                "coupon_code": coupon_code, 
                                "claimed": bool(claimed)
                            })
                        elif not upcoming_spin_rewards:
                            upcoming_spin_rewards.append({"threshold": threshold, "reward": reward_name})
                except Exception as e:
                    logger.warning(f"Error processing spin reward threshold: {e}")
                    continue
                
                # Spend rewards
                current_spend = spend_by_restaurant.get(rid, 0)
                spend_rewards_met = []
                upcoming_spend_rewards = []
                
                try:
                    for th in spend_thresholds:
                        threshold = th.get('amount', 0) if isinstance(th, dict) else 0
                        reward_name = th.get('reward', '') if isinstance(th, dict) else ''
                        
                        if not reward_name:  # Skip if reward name is empty
                            continue
                        
                        # Find claimed reward for this threshold
                        claimed = None
                        try:
                            if rid in rewards_by_restaurant:
                                for cr in rewards_by_restaurant[rid]:
                                    if (hasattr(cr, 'reward_name') and cr.reward_name == reward_name and 
                                        current_spend >= threshold):
                                        claimed = cr
                                        break
                        except Exception as e:
                            logger.warning(f"Error finding claimed reward for spend: {e}")
                            
                        if current_spend >= threshold:
                            coupon_code = getattr(claimed, 'coupon_code', None) if claimed else None
                            spend_rewards_met.append({
                                "threshold": threshold, 
                                "reward": reward_name, 
                                "coupon_code": coupon_code, 
                                "claimed": bool(claimed)
                            })
                        elif not upcoming_spend_rewards:
                            upcoming_spend_rewards.append({"threshold": threshold, "reward": reward_name})
                except Exception as e:
                    logger.warning(f"Error processing spend threshold: {e}")
                    continue
                
                # Safely build the restaurant entry
                restaurant_entry = {
                    "restaurant_id": rid,
                    "restaurant_name": getattr(restaurant, 'restaurant_name', 'Unknown Restaurant'),
                    "spin_progress": {
                        "current_spin_points": current_spin_points,
                        "number_of_spins": num_spins,
                        "rewards_met": spin_rewards_met,
                        "upcoming_rewards": upcoming_spin_rewards
                    },
                    "spend_progress": {
                        "current_spend": current_spend,
                        "rewards_met": spend_rewards_met,
                        "upcoming_rewards": upcoming_spend_rewards
                    },
                    "claimed_rewards": []
                }
                
                # Safely add claimed rewards
                try:
                    if rid in rewards_by_restaurant:
                        claimed_rewards_list = []
                        for cr in rewards_by_restaurant[rid]:
                            # Find the threshold for this reward if possible
                            threshold = None
                            reward_name = getattr(cr, 'reward_name', '')
                            if reward_name:
                                for th in reward_thresholds:
                                    if isinstance(th, dict) and th.get('reward', '') == reward_name:
                                        threshold = th.get('points', None)
                                        break
                            
                            reward_info = {
                                "reward_name": reward_name,
                                "threshold": threshold,
                                "coupon_code": getattr(cr, 'coupon_code', None),
                                "redeemed": getattr(cr, 'redeemed', False),
                                "claimed_at": getattr(cr, 'claimed_at', None)
                            }
                            claimed_rewards_list.append(reward_info)
                        
                        restaurant_entry["claimed_rewards"] = claimed_rewards_list
                except Exception as e:
                    logger.warning(f"Error adding claimed rewards to restaurant {rid}: {e}")
                
                dashboard.append(restaurant_entry)
                
            except Exception as e:
                logger.warning(f"Error processing restaurant {rid}: {e}")
                continue

        return {
            "dashboard": dashboard,
            "loyalties": loyalties,
            "submissions": submissions,
            "claimed_rewards": claimed_rewards,
            "audit_logs": audit_logs,
        }
    except Exception as e:
        logger.error(f"Error in user_dashboard: {e}")
        # Return a minimal response to avoid a complete failure
        return {
            "dashboard": [],
            "loyalties": [],
            "submissions": [],
            "claimed_rewards": [],
            "audit_logs": [],
            "error": str(e)
        }
