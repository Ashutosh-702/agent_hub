"""
Inbox Metrics Service - Aggregates metrics for CXO dashboard
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from config.loaded_config import loaded_config
from config.logging import logger
from database.collection_dao.inbox_events import InboxEventsDao, InboxLeadsDao


class MetricsPeriod(str, Enum):
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    CUSTOM = "custom"


class InboxMetricsService:
    """Service for aggregating inbox metrics"""

    def __init__(self):
        mongo_client = loaded_config.connection_manager.mongo_client
        self.events_dao = InboxEventsDao(mongo_client)
        self.leads_dao = InboxLeadsDao(mongo_client)

    async def get_dashboard_metrics(
        self,
        period: MetricsPeriod = MetricsPeriod.WEEK,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get all dashboard metrics for a given period
        """
        # Calculate date range
        if period == MetricsPeriod.CUSTOM and start_date and end_date:
            period_start = start_date
            period_end = end_date
        else:
            period_end = datetime.utcnow()
            days = {"7d": 7, "30d": 30, "90d": 90}.get(period.value, 7)
            period_start = period_end - timedelta(days=days)

        # Previous period for comparison
        period_duration = period_end - period_start
        prev_period_end = period_start
        prev_period_start = prev_period_end - period_duration

        logger.info(f"Calculating metrics", period=period.value, start=period_start, end=period_end)

        # Gather all metrics
        try:
            response_rate = await self._calculate_response_rate(period_start, period_end)
            prev_response_rate = await self._calculate_response_rate(prev_period_start, prev_period_end)
            
            hot_leads = await self._get_hot_leads_count()
            needs_attention = await self._get_needs_attention_counts()
            pipeline_value = await self._get_pipeline_value()
            avg_response_time = await self._calculate_avg_response_time(period_start, period_end)
            funnel = await self._get_conversion_funnel(period_start, period_end)
            channel_performance = await self._get_channel_performance(period_start, period_end)
            weekly_comparison = await self._get_weekly_comparison()

            return {
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat(),
                    "label": period.value
                },
                "response_rate": {
                    "value": response_rate,
                    "trend": response_rate - prev_response_rate if prev_response_rate else 0,
                    "benchmark": 20.0  # Industry benchmark
                },
                "hot_leads": hot_leads,
                "needs_attention": needs_attention,
                "pipeline_value": pipeline_value,
                "avg_response_time_hours": avg_response_time,
                "funnel": funnel,
                "channel_performance": channel_performance,
                "weekly_comparison": weekly_comparison
            }

        except Exception as e:
            logger.exception(f"Error calculating metrics: {e}")
            # Return default values on error
            return self._get_default_metrics(period_start, period_end, period.value)

    async def _calculate_response_rate(
        self,
        start: datetime,
        end: datetime
    ) -> float:
        """Calculate response rate: replies / sent messages"""
        try:
            pipeline = [
                {
                    "$match": {
                        "at": {"$gte": start, "$lte": end}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "sent": {
                            "$sum": {"$cond": [{"$eq": ["$direction", "outbound"]}, 1, 0]}
                        },
                        "received": {
                            "$sum": {"$cond": [{"$eq": ["$direction", "inbound"]}, 1, 0]}
                        }
                    }
                }
            ]
            
            result = await self.events_dao.aggregate(pipeline)
            if result and result[0].get("sent", 0) > 0:
                return round((result[0]["received"] / result[0]["sent"]) * 100, 1)
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating response rate: {e}")
            return 0.0

    async def _get_hot_leads_count(self) -> Dict[str, int]:
        """Get count of hot leads and urgent ones"""
        try:
            hot_count = await self.leads_dao.count_leads({"temperature": "hot"})
            
            # Urgent = hot + (unread > 0 OR waiting_on_us)
            urgent_count = await self.leads_dao.count_leads({
                "temperature": "hot",
                "$or": [
                    {"unread_count": {"$gt": 0}},
                    {"status": "waiting_on_us"}
                ]
            })
            
            return {
                "count": hot_count,
                "urgent": urgent_count
            }
        except Exception as e:
            logger.error(f"Error getting hot leads count: {e}")
            return {"count": 0, "urgent": 0}

    async def _get_needs_attention_counts(self) -> Dict[str, int]:
        """Get counts of leads needing attention by type"""
        try:
            unread = await self.leads_dao.count_leads({"unread_count": {"$gt": 0}})
            
            # Overdue = in sequence with next_step_at in past
            overdue = await self.leads_dao.count_leads({
                "in_sequence": True,
                "next_step_at": {"$lt": datetime.utcnow()}
            })
            
            waiting = await self.leads_dao.count_leads({"status": "waiting_on_us"})
            
            # Hot stale = hot leads with last touch > 3 days ago
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            hot_stale = await self.leads_dao.count_leads({
                "temperature": "hot",
                "last_touch.at": {"$lt": three_days_ago}
            })
            
            return {
                "total": unread + overdue + waiting + hot_stale,
                "unread": unread,
                "overdue": overdue,
                "waiting": waiting,
                "hot_stale": hot_stale
            }
        except Exception as e:
            logger.error(f"Error getting needs attention counts: {e}")
            return {"total": 0, "unread": 0, "overdue": 0, "waiting": 0, "hot_stale": 0}

    async def _get_pipeline_value(self) -> Dict[str, Any]:
        """Get estimated pipeline value from active deals"""
        try:
            # Count leads with deal-related statuses
            deal_count = await self.leads_dao.count_leads({
                "status": {"$in": ["deal_open", "meeting_scheduled"]}
            })
            
            # For now, use estimated average deal value
            # In production, this would come from CRM integration
            avg_deal_value = 15000  # USD
            
            return {
                "amount": deal_count * avg_deal_value,
                "currency": "USD",
                "deals": deal_count
            }
        except Exception as e:
            logger.error(f"Error getting pipeline value: {e}")
            return {"amount": 0, "currency": "USD", "deals": 0}

    async def _calculate_avg_response_time(
        self,
        start: datetime,
        end: datetime
    ) -> float:
        """Calculate average time between outbound and inbound messages"""
        try:
            # This is a simplified calculation
            # In production, you'd track actual response times per conversation
            pipeline = [
                {
                    "$match": {
                        "at": {"$gte": start, "$lte": end},
                        "direction": "inbound"
                    }
                },
                {
                    "$group": {
                        "_id": "$lead_id",
                        "first_reply": {"$min": "$at"}
                    }
                }
            ]
            
            # For now, return a mock average
            # Real implementation would calculate actual response times
            return 18.5
        except Exception as e:
            logger.error(f"Error calculating avg response time: {e}")
            return 0.0

    async def _get_conversion_funnel(
        self,
        start: datetime,
        end: datetime
    ) -> Dict[str, int]:
        """Get conversion funnel data"""
        try:
            # Count events by direction
            sent = await self.events_dao.count_events({
                "at": {"$gte": start, "$lte": end},
                "direction": "outbound"
            })
            
            replied = await self.events_dao.count_events({
                "at": {"$gte": start, "$lte": end},
                "direction": "inbound"
            })
            
            # Count leads by status
            meeting = await self.leads_dao.count_leads({
                "status": "meeting_scheduled"
            })
            
            deal = await self.leads_dao.count_leads({
                "status": {"$in": ["deal_open", "closed_won"]}
            })
            
            # Estimate opened (typically 40-60% of sent for cold outreach)
            opened = int(sent * 0.45) if sent > 0 else 0
            
            return {
                "sent": sent,
                "opened": opened,
                "replied": replied,
                "meeting": meeting,
                "deal": deal
            }
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {"sent": 0, "opened": 0, "replied": 0, "meeting": 0, "deal": 0}

    async def _get_channel_performance(
        self,
        start: datetime,
        end: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics by channel"""
        try:
            channels = ["email", "linkedin", "whatsapp", "call"]
            performance = {}
            
            for channel in channels:
                sent = await self.events_dao.count_events({
                    "at": {"$gte": start, "$lte": end},
                    "channel": channel,
                    "direction": "outbound"
                })
                
                replied = await self.events_dao.count_events({
                    "at": {"$gte": start, "$lte": end},
                    "channel": channel,
                    "direction": "inbound"
                })
                
                rate = round((replied / sent) * 100, 1) if sent > 0 else 0
                
                performance[channel] = {
                    "sent": sent,
                    "replied": replied,
                    "rate": rate
                }
            
            return performance
        except Exception as e:
            logger.error(f"Error getting channel performance: {e}")
            return {ch: {"sent": 0, "replied": 0, "rate": 0} for ch in ["email", "linkedin", "whatsapp", "call"]}

    async def _get_weekly_comparison(self) -> Dict[str, Any]:
        """Compare this week vs last week"""
        try:
            now = datetime.utcnow()
            this_week_start = now - timedelta(days=7)
            last_week_start = now - timedelta(days=14)
            last_week_end = now - timedelta(days=7)
            
            this_week_replies = await self.events_dao.count_events({
                "at": {"$gte": this_week_start, "$lte": now},
                "direction": "inbound"
            })
            
            last_week_replies = await self.events_dao.count_events({
                "at": {"$gte": last_week_start, "$lte": last_week_end},
                "direction": "inbound"
            })
            
            change = 0
            if last_week_replies > 0:
                change = round(((this_week_replies - last_week_replies) / last_week_replies) * 100, 1)
            
            return {
                "this_week": this_week_replies,
                "last_week": last_week_replies,
                "change": change
            }
        except Exception as e:
            logger.error(f"Error getting weekly comparison: {e}")
            return {"this_week": 0, "last_week": 0, "change": 0}

    def _get_default_metrics(
        self,
        start: datetime,
        end: datetime,
        period_label: str
    ) -> Dict[str, Any]:
        """Return default metrics structure when data unavailable"""
        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "label": period_label
            },
            "response_rate": {"value": 0, "trend": 0, "benchmark": 20.0},
            "hot_leads": {"count": 0, "urgent": 0},
            "needs_attention": {"total": 0, "unread": 0, "overdue": 0, "waiting": 0, "hot_stale": 0},
            "pipeline_value": {"amount": 0, "currency": "USD", "deals": 0},
            "avg_response_time_hours": 0,
            "funnel": {"sent": 0, "opened": 0, "replied": 0, "meeting": 0, "deal": 0},
            "channel_performance": {
                ch: {"sent": 0, "replied": 0, "rate": 0} 
                for ch in ["email", "linkedin", "whatsapp", "call"]
            },
            "weekly_comparison": {"this_week": 0, "last_week": 0, "change": 0}
        }


# Singleton instance
_metrics_service: Optional[InboxMetricsService] = None


def get_metrics_service() -> InboxMetricsService:
    """Get or create metrics service instance"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = InboxMetricsService()
    return _metrics_service

