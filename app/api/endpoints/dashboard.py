from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ... import schemas, crud
from ...database import get_db
from typing import List

router = APIRouter(prefix="/api/userdashboard", tags=["userdashboard"])

@router.get("/")
def user_dashboard(uid: str, db: Session = Depends(get_db)):
    loyalties = crud.list_loyalties(db, uid=uid)
    submissions = crud.list_submissions(db, uid=uid)
    claimed_rewards = crud.list_claimed_rewards(db, uid=uid)
    audit_logs = crud.list_audit_logs(db, uid=uid)

    # Organize claimed rewards by restaurant
    rewards_by_restaurant = {}
    for reward in claimed_rewards:
        rid = reward.restaurant_id
        rewards_by_restaurant.setdefault(rid, []).append(reward)

    # Organize submissions by restaurant for spend
    spend_by_restaurant = {}
    for sub in submissions:
        rid = sub.restaurant_id
        spend_by_restaurant[rid] = spend_by_restaurant.get(rid, 0) + (sub.amount_spent or 0)

    dashboard = []
    restaurant_ids = set(list(rewards_by_restaurant.keys()) + list(spend_by_restaurant.keys()))
    for rid in restaurant_ids:
        restaurant = crud.get_restaurant(db, rid)
        if not restaurant:
            continue
        # Spin stats
        points_per_spin = getattr(restaurant, 'points_per_spin', 1)
        num_spins = len(rewards_by_restaurant.get(rid, []))
        current_spin_points = num_spins * points_per_spin
        spin_thresholds = sorted(restaurant.reward_thresholds, key=lambda x: x.get('points', 0))
        spend_thresholds = sorted(restaurant.spend_thresholds, key=lambda x: x.get('amount', 0))
        # Which spin rewards met
        spin_rewards_met = []
        upcoming_spin_rewards = []
        for th in spin_thresholds:
            threshold = th.get('points', 0)
            reward_name = th.get('reward', '')
            # Find claimed reward for this threshold
            claimed = next((cr for cr in rewards_by_restaurant.get(rid, []) if cr.reward_name == reward_name and points_per_spin * len(rewards_by_restaurant[rid]) >= threshold), None)
            if current_spin_points >= threshold:
                spin_rewards_met.append({"threshold": threshold, "reward": reward_name, "coupon_code": claimed.coupon_code if claimed else None, "claimed": bool(claimed)})
            elif not upcoming_spin_rewards:
                upcoming_spin_rewards.append({"threshold": threshold, "reward": reward_name})
        # Spend rewards
        current_spend = spend_by_restaurant.get(rid, 0)
        spend_rewards_met = []
        upcoming_spend_rewards = []
        for th in spend_thresholds:
            threshold = th.get('amount', 0)
            reward_name = th.get('reward', '')
            # Find claimed reward for this threshold
            claimed = next((cr for cr in rewards_by_restaurant.get(rid, []) if cr.reward_name == reward_name and current_spend >= threshold), None)
            if current_spend >= threshold:
                spend_rewards_met.append({"threshold": threshold, "reward": reward_name, "coupon_code": claimed.coupon_code if claimed else None, "claimed": bool(claimed)})
            elif not upcoming_spend_rewards:
                upcoming_spend_rewards.append({"threshold": threshold, "reward": reward_name})
        dashboard.append({
            "restaurant_id": rid,
            "restaurant_name": restaurant.restaurant_name,
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
            "claimed_rewards": [
                {
                    "reward_name": cr.reward_name,
                    "threshold": next((th.get('points', 0) for th in spin_thresholds if th.get('reward', '') == cr.reward_name), None),
                    "coupon_code": cr.coupon_code,
                    "redeemed": cr.redeemed,
                    "claimed_at": cr.claimed_at
                } for cr in rewards_by_restaurant.get(rid, [])
            ]
        })
    return {
        "dashboard": dashboard,
        "loyalties": loyalties,
        "submissions": submissions,
        "claimed_rewards": claimed_rewards,
        "audit_logs": audit_logs,
    }
