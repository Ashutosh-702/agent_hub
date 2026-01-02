"""
Inbox API Routes
FastAPI routes for unified inbox operations
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Body
from fastapi.responses import ORJSONResponse

from ai_agents.inbox.models import (
    Channel, Temperature, LeadStatus, StageStatus,
    ListLeadsParams, ListLeadsResponse, LeadDetail,
    UpdateLeadRequest, UpdateSequenceRequest, AddNoteRequest,
    AttentionReason
)
from ai_agents.inbox.service import get_inbox_service
from ai_agents.inbox.metrics_service import get_metrics_service, MetricsPeriod
from ai_agents.inbox.inboxy_service import get_inboxy_service
from config.logging import logger


router = APIRouter(prefix="/inbox", tags=["Inbox"])


@router.get("/leads", response_model=ListLeadsResponse)
async def list_leads(
    query: Optional[str] = Query(None, description="Search query for company/contact"),
    channel: Optional[Channel] = Query(None, description="Filter by channel"),
    temperature: Optional[Temperature] = Query(None, description="Filter by temperature"),
    status: Optional[LeadStatus] = Query(None, description="Filter by status"),
    in_sequence: Optional[str] = Query("any", description="Filter by sequence: any, yes, no"),
    stage_status: Optional[StageStatus] = Query(None, description="Filter by sequence stage status"),
    owner_email: Optional[str] = Query(None, description="Filter by owner email"),
    sort: Optional[str] = Query("recent", description="Sort: recent, attention, hot"),
    tab: Optional[str] = Query("all", description="Tab: all, attention, sequence"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List leads with filters and pagination.
    
    Tabs:
    - all: All leads
    - attention: Leads needing attention (unread, overdue, waiting)
    - sequence: Leads currently in a sequence
    """
    try:
        service = get_inbox_service()
        
        params = ListLeadsParams(
            query=query,
            channel=channel,
            temperature=temperature,
            status=status,
            in_sequence=in_sequence,
            stage_status=stage_status,
            owner_email=owner_email,
            sort=sort,
            tab=tab,
            page=page,
            page_size=page_size
        )
        
        result = await service.list_leads(params)
        
        # Add attention reasons to response if tab is "attention"
        if tab == "attention":
            for lead in result.leads:
                lead.attention_reasons = service.compute_needs_attention(lead)
        
        return result
        
    except Exception as e:
        logger.exception(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads/{lead_id}", response_model=LeadDetail)
async def get_lead_detail(lead_id: str):
    """
    Get full lead detail including timeline events and notes.
    """
    try:
        service = get_inbox_service()
        result = await service.get_lead_detail(lead_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting lead detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, update: UpdateLeadRequest):
    """
    Update lead temperature and/or status.
    """
    try:
        service = get_inbox_service()
        
        # Verify lead exists
        lead = await service.get_lead_detail(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        success = await service.update_lead(lead_id, update)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update lead")
        
        return ORJSONResponse({"success": True, "message": "Lead updated"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/{lead_id}/read")
async def mark_lead_read(lead_id: str):
    """
    Mark all messages for a lead as read.
    """
    try:
        service = get_inbox_service()
        
        # Verify lead exists
        lead = await service.get_lead_detail(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        success = await service.mark_lead_read(lead_id)
        
        return ORJSONResponse({"success": True, "message": "Marked as read"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error marking lead read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/leads/{lead_id}/sequence")
async def update_sequence(lead_id: str, update: UpdateSequenceRequest):
    """
    Update sequence enrollment (pause/resume).
    """
    try:
        service = get_inbox_service()
        
        # Verify lead exists
        lead = await service.get_lead_detail(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        if not lead.summary.in_sequence:
            raise HTTPException(status_code=400, detail="Lead is not in a sequence")
        
        # TODO: Implement sequence pause/resume
        return ORJSONResponse({"success": True, "message": "Sequence updated"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leads/{lead_id}/notes")
async def add_note(lead_id: str, note: AddNoteRequest):
    """
    Add a note to a lead.
    """
    try:
        service = get_inbox_service()
        
        # Verify lead exists
        lead = await service.get_lead_detail(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # TODO: Get actual author from auth context
        author = "Current User"
        
        note_id = await service.add_note(lead_id, author, note.text)
        
        return ORJSONResponse({
            "success": True,
            "note_id": note_id,
            "message": "Note added"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error adding note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def trigger_sync(full_sync: bool = Query(False, description="Perform full sync")):
    """
    Trigger a sync with Lemlist API.
    """
    try:
        service = get_inbox_service()
        stats = await service.sync_from_lemlist(full_sync=full_sync)
        
        return ORJSONResponse({
            "success": True,
            "stats": stats,
            "message": "Sync completed"
        })
        
    except Exception as e:
        logger.exception(f"Error during sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attention-reasons/{lead_id}")
async def get_attention_reasons(lead_id: str):
    """
    Get attention reasons for a specific lead.
    """
    try:
        service = get_inbox_service()
        lead = await service.get_lead_detail(lead_id)
        
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        reasons = service.compute_needs_attention(lead.summary)
        
        return ORJSONResponse({
            "lead_id": lead_id,
            "reasons": [r.dict() for r in reasons]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting attention reasons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Dashboard Metrics ============

@router.get("/metrics")
async def get_dashboard_metrics(
    period: str = Query("7d", description="Period: 7d, 30d, 90d, or custom"),
    start_date: Optional[str] = Query(None, description="Start date for custom period (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date for custom period (ISO format)")
):
    """
    Get dashboard metrics for CXO view.
    
    Returns:
    - Response rate with trend
    - Hot leads count
    - Needs attention breakdown
    - Pipeline value
    - Conversion funnel
    - Channel performance
    - Weekly comparison
    """
    try:
        service = get_metrics_service()
        
        # Parse period
        try:
            metrics_period = MetricsPeriod(period)
        except ValueError:
            metrics_period = MetricsPeriod.WEEK
        
        # Parse dates for custom period
        parsed_start = None
        parsed_end = None
        if metrics_period == MetricsPeriod.CUSTOM:
            if start_date:
                parsed_start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if end_date:
                parsed_end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        metrics = await service.get_dashboard_metrics(
            period=metrics_period,
            start_date=parsed_start,
            end_date=parsed_end
        )
        
        return ORJSONResponse(metrics)
        
    except Exception as e:
        logger.exception(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Inboxy AI Recommendations ============

@router.get("/recommendations")
async def get_recommendations(
    limit: int = Query(5, ge=1, le=10, description="Number of recommendations to return")
):
    """
    Get AI-powered recommendations from Inboxy.
    
    Returns actionable insights for CXO/Founders:
    - Priority leads to focus on
    - Follow-up alerts
    - Channel insights
    - Risk alerts
    - Performance insights
    """
    try:
        # Get metrics context for recommendations
        metrics_service = get_metrics_service()
        metrics = await metrics_service.get_dashboard_metrics(MetricsPeriod.WEEK)
        
        # Get recommendations with context
        inboxy_service = get_inboxy_service()
        recommendations = await inboxy_service.get_recommendations(
            context={
                "weekly_comparison": metrics.get("weekly_comparison", {}),
                "needs_attention": metrics.get("needs_attention", {}),
                "hot_leads": metrics.get("hot_leads", {}),
                "response_rate": metrics.get("response_rate", {})
            },
            limit=limit
        )
        
        return ORJSONResponse(recommendations)
        
    except Exception as e:
        logger.exception(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

