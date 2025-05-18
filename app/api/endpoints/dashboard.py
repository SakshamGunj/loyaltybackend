from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from typing import List, Dict, Any, Optional
import logging

router = APIRouter(prefix="/api/userdashboard", tags=["userdashboard"])

# Set up logger
logger = logging.getLogger(__name__)

@router.get("/", response_model=schemas.UserDashboardResponse)
def user_dashboard(uid: str, db: Session = Depends(get_db)):
    """
    Get consolidated user dashboard data, including profile, orders, general loyalty/rewards,
    and detailed per-restaurant progress.
    """
    try:
        # --- Primary Data Fetch using get_user_dashboard_data ---
        comprehensive_user_data = crud.get_user_dashboard_data(db, user_uid=uid)

        if not comprehensive_user_data:
            logger.info(f"User dashboard data requested for non-existent or empty data user UID: {uid}")
            raise HTTPException(status_code=404, detail="User not found or no dashboard data available")

        user_profile = comprehensive_user_data.get("profile")
        user_orders = comprehensive_user_data.get("orders", [])
        general_loyalty_info = comprehensive_user_data.get("loyalty_info", [])
        general_claimed_rewards = comprehensive_user_data.get("claimed_rewards", [])

        # --- Fetch additional data needed for existing logic or direct inclusion ---
        # Submissions are needed for spend_by_restaurant calculation.
        submissions = crud.list_submissions(db, uid=uid)
        # Audit logs are part of the desired final response.
        audit_logs = crud.list_audit_logs(db, uid=uid)

        # --- Existing Per-Restaurant Progress Logic ---
        # Organize claimed rewards by restaurant using general_claimed_rewards
        rewards_by_restaurant = {}
        for reward in general_claimed_rewards: # Using the list from comprehensive_user_data
            if not hasattr(reward, 'restaurant_id') or not reward.restaurant_id:
                logger.warning(f"Missing restaurant_id for reward {getattr(reward, 'id', 'unknown')}")
                continue
            rid = reward.restaurant_id
            if rid not in rewards_by_restaurant:
                rewards_by_restaurant[rid] = []
            rewards_by_restaurant[rid].append(reward)

        # Organize submissions by restaurant for spend
        spend_by_restaurant = {}
        for sub in submissions: # submissions are fetched above
            try:
                if not hasattr(sub, 'restaurant_id') or not sub.restaurant_id:
                    logger.warning(f"Missing restaurant_id for submission {getattr(sub, 'submission_id', 'unknown')}")
                    continue
                rid = sub.restaurant_id
                amount_spent = getattr(sub, 'amount_spent', 0) or 0
                spend_by_restaurant[rid] = spend_by_restaurant.get(rid, 0) + amount_spent
            except Exception as e:
                logger.warning(f"Error processing submission for spend_by_restaurant: {e}")
                continue
        
        restaurant_specific_progress_list = []
        # Get unique restaurant IDs from both sources
        # Ensure keys from spend_by_restaurant are included even if no rewards for that restaurant
        restaurant_ids_for_progress = set(list(rewards_by_restaurant.keys()) + list(spend_by_restaurant.keys()))
        
        for rid in restaurant_ids_for_progress:
            try:
                restaurant_model = crud.get_restaurant(db, rid) # Renamed to avoid conflict
                if not restaurant_model:
                    logger.warning(f"Restaurant not found for ID during progress calculation: {rid}")
                    continue
                
                reward_thresholds = []
                try:
                    if hasattr(restaurant_model, 'reward_thresholds') and restaurant_model.reward_thresholds:
                        if isinstance(restaurant_model.reward_thresholds, list):
                            reward_thresholds = sorted(
                                [t for t in restaurant_model.reward_thresholds if isinstance(t, dict)], # Ensure items are dicts
                                key=lambda x: x.get('points', 0)
                            )
                except Exception as e:
                    logger.warning(f"Error processing reward thresholds for restaurant {rid}: {e}")
                
                spend_thresholds = []
                try:
                    if hasattr(restaurant_model, 'spend_thresholds') and restaurant_model.spend_thresholds:
                        if isinstance(restaurant_model.spend_thresholds, list):
                             spend_thresholds = sorted(
                                [t for t in restaurant_model.spend_thresholds if isinstance(t, dict)], # Ensure items are dicts
                                key=lambda x: x.get('amount', 0)
                            )
                except Exception as e:
                    logger.warning(f"Error processing spend thresholds for restaurant {rid}: {e}")
                
                points_per_spin = getattr(restaurant_model, 'points_per_spin', 1) or 1
                # num_spins should be derived from rewards_by_restaurant[rid] if it exists
                num_spins = len(rewards_by_restaurant.get(rid, []))
                current_spin_points = num_spins * points_per_spin
                
                spin_rewards_met = []
                upcoming_spin_rewards = []
                
                try:
                    for th_data in reward_thresholds: # th_data is a dict from restaurant_model.reward_thresholds
                        threshold_points = th_data.get('points', 0)
                        reward_name = th_data.get('reward', th_data.get('name', '')) # Check 'reward' then 'name'
                        
                        if not reward_name: continue
                        
                        claimed_for_this_threshold = None
                        # Check against general_claimed_rewards filtered by restaurant and matching this threshold's reward_name
                        if rid in rewards_by_restaurant:
                            for cr_in_rest in rewards_by_restaurant[rid]:
                                if hasattr(cr_in_rest, 'reward_name') and cr_in_rest.reward_name == reward_name:
                                    # This check might need to be more robust if threshold_id was stored on ClaimedReward
                                    claimed_for_this_threshold = cr_in_rest
                                    break
                        
                        met_entry = {
                            "threshold": threshold_points, 
                            "reward": reward_name, 
                            "coupon_code": getattr(claimed_for_this_threshold, 'coupon_code', None) if claimed_for_this_threshold else None, 
                            "claimed": bool(claimed_for_this_threshold)
                        }

                        if current_spin_points >= threshold_points:
                            spin_rewards_met.append(met_entry)
                        else:
                            upcoming_spin_rewards.append({"threshold": threshold_points, "reward": reward_name})
                except Exception as e:
                    logger.warning(f"Error processing spin reward threshold for restaurant {rid}: {e}")
                
                current_spend = spend_by_restaurant.get(rid, 0)
                spend_rewards_met = []
                upcoming_spend_rewards = []
                
                try:
                    for th_data in spend_thresholds: # th_data is a dict
                        threshold_amount = th_data.get('amount', 0)
                        reward_name = th_data.get('reward', th_data.get('name', '')) # Check 'reward' then 'name'

                        if not reward_name: continue
                        
                        claimed_for_this_threshold = None
                        if rid in rewards_by_restaurant: # Claimed rewards are general, check if one matches this spend reward
                             for cr_in_rest in rewards_by_restaurant[rid]:
                                if hasattr(cr_in_rest, 'reward_name') and cr_in_rest.reward_name == reward_name:
                                    # This implies spend rewards can also result in entries in ClaimedReward table
                                    claimed_for_this_threshold = cr_in_rest
                                    break
                        
                        met_entry = {
                            "threshold": threshold_amount, 
                            "reward": reward_name, 
                            "coupon_code": getattr(claimed_for_this_threshold, 'coupon_code', None) if claimed_for_this_threshold else None, 
                            "claimed": bool(claimed_for_this_threshold)
                        }

                        if current_spend >= threshold_amount:
                            spend_rewards_met.append(met_entry)
                        else:
                            upcoming_spend_rewards.append({"threshold": threshold_amount, "reward": reward_name})
                except Exception as e:
                    logger.warning(f"Error processing spend threshold for restaurant {rid}: {e}")

                restaurant_entry_data = {
                    "restaurant_id": rid,
                    "restaurant_name": getattr(restaurant_model, 'restaurant_name', 'Unknown Restaurant'),
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
                    "claimed_rewards_for_restaurant": [] # Populated below
                }
                
                # Populate claimed_rewards_for_restaurant for this specific restaurant
                claimed_rewards_at_this_restaurant = []
                if rid in rewards_by_restaurant:
                    for cr_model in rewards_by_restaurant[rid]: # cr_model is models.ClaimedReward
                        # Try to find threshold details (points or amount)
                        # This part remains complex as it tries to cross-reference.
                        cr_threshold_value = None
                        cr_reward_name = getattr(cr_model, 'reward_name', '')
                        # Check against spin thresholds
                        for r_th in reward_thresholds:
                            if r_th.get('reward', r_th.get('name', '')) == cr_reward_name:
                                cr_threshold_value = r_th.get('points')
                                break
                        # If not found, check against spend thresholds
                        if cr_threshold_value is None:
                            for s_th in spend_thresholds:
                                if s_th.get('reward', s_th.get('name', '')) == cr_reward_name:
                                    cr_threshold_value = s_th.get('amount')
                                    break
                        
                        claimed_rewards_at_this_restaurant.append({
                            "reward_name": cr_reward_name,
                            "threshold": cr_threshold_value, # May be None if not perfectly matched
                            "coupon_code": getattr(cr_model, 'coupon_code', None),
                            "redeemed": getattr(cr_model, 'redeemed', False),
                            "claimed_at": getattr(cr_model, 'claimed_at', None)
                        })
                restaurant_entry_data["claimed_rewards_for_restaurant"] = claimed_rewards_at_this_restaurant
                restaurant_specific_progress_list.append(restaurant_entry_data)
                
            except Exception as e:
                logger.error(f"Error processing restaurant progress for {rid}: {e}", exc_info=True)
                continue # Continue to next restaurant if one fails

        # --- Constructing the new final response ---
        return {
            "profile": user_profile,                 # This is a models.User object, Pydantic will serialize
            "orders": user_orders,                   # This is List[Dict] from crud.get_orders_by_user
            "loyalty_info": general_loyalty_info,    # List[models.Loyalty]
            "claimed_rewards": general_claimed_rewards, # List[models.ClaimedReward]
            "restaurant_specific_progress": restaurant_specific_progress_list,
            "audit_logs": audit_logs                 # List[models.AuditLog]
            # Submissions are not directly returned at top level anymore, but used for calculations.
        }
    except HTTPException: # Re-raise HTTPExceptions to let FastAPI handle them
        raise
    except Exception as e:
        logger.error(f"Fatal error in user_dashboard endpoint for UID {uid}: {e}", exc_info=True)
        # Fallback to a standard error response for unhandled exceptions
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
