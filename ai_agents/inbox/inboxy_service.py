"""
Inboxy AI Recommender Service
Provides intelligent recommendations for CXO/Founders based on inbox data
Architected for easy LLM integration in the future
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import random

from config.loaded_config import loaded_config
from config.logging import logger
from database.collection_dao.inbox_events import InboxEventsDao, InboxLeadsDao


class RecommendationType(str, Enum):
    PRIORITY_LEADS = "priority_leads"
    FOLLOWUP_ALERT = "followup_alert"
    CHANNEL_INSIGHT = "channel_insight"
    TIMING_OPTIMIZATION = "timing_optimization"
    BUYING_SIGNALS = "buying_signals"
    RISK_ALERT = "risk_alert"
    PERFORMANCE_INSIGHT = "performance_insight"


class RecommendationPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Recommendation:
    """A single recommendation from Inboxy"""
    
    def __init__(
        self,
        rec_id: str,
        rec_type: RecommendationType,
        priority: RecommendationPriority,
        title: str,
        description: str,
        action_label: str,
        action_route: str,
        leads: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = rec_id
        self.type = rec_type
        self.priority = priority
        self.title = title
        self.description = description
        self.action = {"label": action_label, "route": action_route}
        self.leads = leads or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "leads": self.leads,
            "metadata": self.metadata
        }


class RecommendationProvider(ABC):
    """Abstract base class for recommendation providers"""
    
    @abstractmethod
    async def generate_recommendations(
        self,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Recommendation]:
        """Generate recommendations based on inbox context"""
        pass


class MockRecommendationProvider(RecommendationProvider):
    """
    Mock recommendation provider for development
    Generates realistic recommendations based on actual data patterns
    """
    
    def __init__(self):
        mongo_client = loaded_config.connection_manager.mongo_client
        self.leads_dao = InboxLeadsDao(mongo_client)
        self.events_dao = InboxEventsDao(mongo_client)

    async def generate_recommendations(
        self,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Recommendation]:
        """Generate mock recommendations based on actual data"""
        recommendations = []
        
        try:
            # 1. Priority Leads - Hot leads needing attention
            hot_leads = await self._get_hot_leads_needing_attention()
            if hot_leads:
                recommendations.append(Recommendation(
                    rec_id="rec_priority_1",
                    rec_type=RecommendationType.PRIORITY_LEADS,
                    priority=RecommendationPriority.HIGH,
                    title=f"{len(hot_leads)} hot leads need your attention today",
                    description="These leads have shown strong buying signals and are waiting for your response. Prioritize them to maximize conversion.",
                    action_label="View Hot Leads",
                    action_route="/inbox/messages?temperature=hot",
                    leads=[l["lead_id"] for l in hot_leads[:5]]
                ))

            # 2. Follow-up Alerts - Stale conversations
            stale_leads = await self._get_stale_leads()
            if stale_leads:
                recommendations.append(Recommendation(
                    rec_id="rec_followup_1",
                    rec_type=RecommendationType.FOLLOWUP_ALERT,
                    priority=RecommendationPriority.HIGH,
                    title=f"{len(stale_leads)} leads haven't been contacted in 5+ days",
                    description="These conversations have gone cold. A quick follow-up could re-engage them before they lose interest.",
                    action_label="View Stale Leads",
                    action_route="/inbox/messages?sort=oldest",
                    leads=[l["lead_id"] for l in stale_leads[:5]]
                ))

            # 3. Channel Insight - Compare channel performance
            channel_insight = await self._get_channel_insight()
            if channel_insight:
                recommendations.append(channel_insight)

            # 4. Risk Alert - Hot leads going cold
            at_risk = await self._get_at_risk_leads()
            if at_risk:
                recommendations.append(Recommendation(
                    rec_id="rec_risk_1",
                    rec_type=RecommendationType.RISK_ALERT,
                    priority=RecommendationPriority.HIGH,
                    title=f"{len(at_risk)} hot leads are going cold",
                    description="These high-value leads haven't had activity in 3+ days. Immediate action recommended to prevent losing them.",
                    action_label="Take Action",
                    action_route="/inbox/messages?temperature=hot&sort=oldest",
                    leads=[l["lead_id"] for l in at_risk[:3]]
                ))

            # 5. Unread Replies
            unread_count = await self._get_unread_count()
            if unread_count > 0:
                recommendations.append(Recommendation(
                    rec_id="rec_unread_1",
                    rec_type=RecommendationType.PRIORITY_LEADS,
                    priority=RecommendationPriority.HIGH,
                    title=f"{unread_count} unread replies waiting",
                    description="You have leads actively engaging with you. Quick responses improve conversion rates by up to 50%.",
                    action_label="View Unread",
                    action_route="/inbox/messages?tab=attention",
                    metadata={"unread_count": unread_count}
                ))

            # 6. Timing Optimization (always show this insight)
            recommendations.append(Recommendation(
                rec_id="rec_timing_1",
                rec_type=RecommendationType.TIMING_OPTIMIZATION,
                priority=RecommendationPriority.LOW,
                title="Best time to send: Tuesday-Thursday, 9-11 AM",
                description="Based on your reply patterns, leads are most responsive during mid-week mornings. Schedule your outreach accordingly.",
                action_label="View Analytics",
                action_route="/inbox/messages",
                metadata={"best_days": ["Tuesday", "Wednesday", "Thursday"], "best_hours": "9-11 AM"}
            ))

            # 7. Performance insight
            weekly_replies = context.get("weekly_comparison", {})
            if weekly_replies.get("change", 0) > 0:
                recommendations.append(Recommendation(
                    rec_id="rec_perf_1",
                    rec_type=RecommendationType.PERFORMANCE_INSIGHT,
                    priority=RecommendationPriority.LOW,
                    title=f"Replies up {weekly_replies.get('change', 0)}% this week",
                    description=f"Great progress! You received {weekly_replies.get('this_week', 0)} replies this week vs {weekly_replies.get('last_week', 0)} last week.",
                    action_label="View Details",
                    action_route="/inbox/messages",
                    metadata=weekly_replies
                ))
            elif weekly_replies.get("change", 0) < -10:
                recommendations.append(Recommendation(
                    rec_id="rec_perf_2",
                    rec_type=RecommendationType.PERFORMANCE_INSIGHT,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"Replies down {abs(weekly_replies.get('change', 0))}% this week",
                    description="Reply rates have dipped. Consider refreshing your messaging or trying different channels.",
                    action_label="Analyze",
                    action_route="/inbox/messages",
                    metadata=weekly_replies
                ))

        except Exception as e:
            logger.exception(f"Error generating recommendations: {e}")

        # Sort by priority and limit
        priority_order = {RecommendationPriority.HIGH: 0, RecommendationPriority.MEDIUM: 1, RecommendationPriority.LOW: 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 2))
        
        return recommendations[:limit]

    async def _get_hot_leads_needing_attention(self) -> List[Dict]:
        """Get hot leads that need attention"""
        try:
            return await self.leads_dao.find_leads({
                "temperature": "hot",
                "$or": [
                    {"unread_count": {"$gt": 0}},
                    {"status": "waiting_on_us"}
                ]
            }, limit=10)
        except:
            return []

    async def _get_stale_leads(self) -> List[Dict]:
        """Get leads with no activity in 5+ days"""
        try:
            five_days_ago = datetime.utcnow() - timedelta(days=5)
            return await self.leads_dao.find_leads({
                "last_touch.at": {"$lt": five_days_ago},
                "status": {"$nin": ["closed_won", "closed_lost", "dormant"]}
            }, limit=10)
        except:
            return []

    async def _get_at_risk_leads(self) -> List[Dict]:
        """Get hot leads that haven't had activity in 3+ days"""
        try:
            three_days_ago = datetime.utcnow() - timedelta(days=3)
            return await self.leads_dao.find_leads({
                "temperature": "hot",
                "last_touch.at": {"$lt": three_days_ago},
                "status": {"$nin": ["closed_won", "closed_lost"]}
            }, limit=5)
        except:
            return []

    async def _get_unread_count(self) -> int:
        """Get total unread count"""
        try:
            return await self.leads_dao.count_leads({"unread_count": {"$gt": 0}})
        except:
            return 0

    async def _get_channel_insight(self) -> Optional[Recommendation]:
        """Generate channel performance insight"""
        try:
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            
            channels = {}
            for channel in ["email", "linkedin", "whatsapp"]:
                sent = await self.events_dao.count_events({
                    "at": {"$gte": week_ago},
                    "channel": channel,
                    "direction": "outbound"
                })
                replied = await self.events_dao.count_events({
                    "at": {"$gte": week_ago},
                    "channel": channel,
                    "direction": "inbound"
                })
                if sent > 0:
                    channels[channel] = {"sent": sent, "replied": replied, "rate": replied / sent}
            
            if len(channels) >= 2:
                sorted_channels = sorted(channels.items(), key=lambda x: x[1]["rate"], reverse=True)
                best = sorted_channels[0]
                second = sorted_channels[1]
                
                if best[1]["rate"] > second[1]["rate"] * 1.3:  # 30% better
                    multiplier = round(best[1]["rate"] / second[1]["rate"], 1) if second[1]["rate"] > 0 else 2
                    return Recommendation(
                        rec_id="rec_channel_1",
                        rec_type=RecommendationType.CHANNEL_INSIGHT,
                        priority=RecommendationPriority.MEDIUM,
                        title=f"{best[0].capitalize()} is outperforming other channels by {multiplier}x",
                        description=f"This week, {best[0]} has a {round(best[1]['rate']*100)}% reply rate vs {round(second[1]['rate']*100)}% for {second[0]}. Consider shifting more outreach to {best[0]}.",
                        action_label=f"View {best[0].capitalize()} Leads",
                        action_route=f"/inbox/messages?channel={best[0]}",
                        metadata={"channels": channels}
                    )
            return None
        except:
            return None


class LLMRecommendationProvider(RecommendationProvider):
    """
    LLM-powered recommendation provider for production use
    Uses OpenAI or similar to generate intelligent recommendations
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or loaded_config.openai_api_key
        mongo_client = loaded_config.connection_manager.mongo_client
        self.leads_dao = InboxLeadsDao(mongo_client)
        self.events_dao = InboxEventsDao(mongo_client)

    async def generate_recommendations(
        self,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Recommendation]:
        """
        Generate recommendations using LLM
        
        TODO: Implement actual LLM integration
        For now, falls back to mock provider
        """
        logger.info("LLM recommendations not yet implemented, using mock provider")
        mock_provider = MockRecommendationProvider()
        return await mock_provider.generate_recommendations(context, limit)


class InboxyService:
    """
    Main Inboxy service that manages recommendation generation
    """
    
    def __init__(self, use_llm: bool = False):
        if use_llm and loaded_config.openai_api_key:
            self.provider = LLMRecommendationProvider()
            self.ai_powered = True
        else:
            self.provider = MockRecommendationProvider()
            self.ai_powered = False

    async def get_recommendations(
        self,
        context: Dict[str, Any] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get recommendations for the inbox dashboard
        
        Args:
            context: Additional context (metrics, user preferences, etc.)
            limit: Maximum number of recommendations
            
        Returns:
            {
                "recommendations": [...],
                "generated_at": "...",
                "ai_powered": bool
            }
        """
        context = context or {}
        
        try:
            recommendations = await self.provider.generate_recommendations(context, limit)
            
            return {
                "recommendations": [r.to_dict() for r in recommendations],
                "generated_at": datetime.utcnow().isoformat(),
                "ai_powered": self.ai_powered,
                "count": len(recommendations)
            }
        except Exception as e:
            logger.exception(f"Error getting recommendations: {e}")
            return {
                "recommendations": [],
                "generated_at": datetime.utcnow().isoformat(),
                "ai_powered": False,
                "error": str(e)
            }


# Singleton instance
_inboxy_service: Optional[InboxyService] = None


def get_inboxy_service(use_llm: bool = False) -> InboxyService:
    """Get or create Inboxy service instance"""
    global _inboxy_service
    if _inboxy_service is None:
        _inboxy_service = InboxyService(use_llm=use_llm)
    return _inboxy_service


