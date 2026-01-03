"""FastAPI routes for the meetings/client calls module."""

from fastapi import APIRouter, HTTPException, Query, WebSocket, UploadFile, File
from fastapi.responses import ORJSONResponse
from typing import Optional

from app.routing import CustomRequestRoute
from ai_agents.meetings.models import (
    CreateMeetingRequest,
    UpdateMeetingRequest,
    UpdateManualReflectionsRequest,
)
from ai_agents.meetings.service import meeting_service
from ai_agents.meetings.websocket import meeting_websocket_endpoint

# REST API Router
router = APIRouter(
    prefix="/meetings",
    tags=["Meetings / Client Calls"],
    route_class=CustomRequestRoute,
)

# WebSocket Router (separate to avoid route_class issues)
ws_router = APIRouter(tags=["Meetings WebSocket"])


# ============ Meeting CRUD ============

@router.post("")
async def create_meeting(request: CreateMeetingRequest):
    """Create a new meeting record."""
    try:
        meeting = await meeting_service.create_meeting(request)
        return ORJSONResponse(
            status_code=201,
            content={"success": True, "data": meeting}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def get_meetings(
    status: Optional[str] = Query(None, description="Filter by status"),
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Get meetings with optional filters and pagination."""
    try:
        result = await meeting_service.get_meetings(
            status=status,
            company_id=company_id,
            page=page,
            limit=limit,
        )
        return ORJSONResponse(content={"success": True, "data": result})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/completed")
async def get_completed_meetings():
    """Get all completed meetings (for reflections history)."""
    try:
        meetings = await meeting_service.get_completed_meetings()
        return ORJSONResponse(content={"success": True, "data": meetings})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-company/{company_id}")
async def get_meetings_by_company(company_id: str):
    """Get all meetings for a specific company."""
    try:
        meetings = await meeting_service.get_meetings_by_company(company_id)
        return ORJSONResponse(content={"success": True, "data": meetings})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get a specific meeting by ID."""
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return ORJSONResponse(content={"success": True, "data": meeting})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/by-uuid/{meeting_uuid}")
async def get_meeting_by_uuid(meeting_uuid: str):
    """Get a meeting by its UUID."""
    try:
        meeting = await meeting_service.get_meeting_by_uuid(meeting_uuid)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return ORJSONResponse(content={"success": True, "data": meeting})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{meeting_id}")
async def update_meeting(meeting_id: str, request: UpdateMeetingRequest):
    """Update a meeting."""
    try:
        meeting = await meeting_service.update_meeting(meeting_id, request)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return ORJSONResponse(content={"success": True, "data": meeting})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Soft delete a meeting."""
    try:
        deleted = await meeting_service.delete_meeting(meeting_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return ORJSONResponse(content={"success": True, "message": "Meeting deleted"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Meeting Actions ============

@router.post("/{meeting_id}/start")
async def start_meeting(meeting_id: str):
    """
    Get WebSocket connection info to start a live meeting.
    
    Returns the WebSocket URL for connecting to the live transcription.
    """
    try:
        result = await meeting_service.start_meeting(meeting_id)
        return ORJSONResponse(content={"success": True, "data": result})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Battlecard ============

@router.post("/{meeting_id}/battlecard")
async def generate_battlecard(meeting_id: str):
    """Generate a battlecard for meeting preparation."""
    try:
        battlecard = await meeting_service.generate_battlecard(meeting_id)
        return ORJSONResponse(content={"success": True, "data": battlecard})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{meeting_id}/battlecard")
async def get_battlecard(meeting_id: str):
    """Get the battlecard for a meeting."""
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        battlecard = meeting.get("battlecard")
        if not battlecard:
            raise HTTPException(status_code=404, detail="Battlecard not generated yet")
        return ORJSONResponse(content={"success": True, "data": battlecard})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Reflections ============

@router.post("/{meeting_id}/reflections/generate")
async def generate_reflections(meeting_id: str):
    """Generate or regenerate AI reflections for a meeting."""
    try:
        reflections = await meeting_service.generate_reflections(meeting_id)
        return ORJSONResponse(content={"success": True, "data": reflections})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{meeting_id}/reflections")
async def get_reflections(meeting_id: str):
    """Get reflections for a meeting."""
    try:
        reflections = await meeting_service.get_reflections(meeting_id)
        if reflections is None:
            meeting = await meeting_service.get_meeting(meeting_id)
            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting not found")
            return ORJSONResponse(content={"success": True, "data": None})
        return ORJSONResponse(content={"success": True, "data": reflections})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{meeting_id}/reflections/manual")
async def update_manual_reflections(
    meeting_id: str,
    request: UpdateManualReflectionsRequest,
):
    """Update manual reflections for a meeting."""
    try:
        reflections = await meeting_service.update_manual_reflections(meeting_id, request)
        return ORJSONResponse(content={"success": True, "data": reflections})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Audio Transcription ============

@router.post("/{meeting_id}/transcribe-audio")
async def transcribe_audio_file(
    meeting_id: str,
    audio_file: UploadFile = File(..., description="Audio file to transcribe"),
):
    """
    Upload and transcribe an audio file for a meeting.
    
    This endpoint is used for logging existing phone calls by uploading
    a recorded audio file and transcribing it.
    """
    try:
        # Validate file type
        valid_types = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/webm']
        if audio_file.content_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Supported types: {', '.join(valid_types)}"
            )
        
        # Read audio file
        audio_data = await audio_file.read()
        
        # Transcribe using meeting service
        transcript = await meeting_service.transcribe_audio_file(meeting_id, audio_data, audio_file.filename)
        
        return ORJSONResponse(
            content={
                "success": True,
                "data": {
                    "message": "Audio transcribed successfully",
                    "transcript_length": len(transcript) if transcript else 0,
                }
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Context & Summary Generation ============

@router.get("/{meeting_id}/context")
async def get_meeting_context(meeting_id: str):
    """
    Generate or retrieve meeting context for a live call.
    
    This endpoint uses OpenAI to generate contextual information
    about the company, contacts, and products for the meeting.
    """
    try:
        context = await meeting_service.get_meeting_context(meeting_id)
        return ORJSONResponse(content={"success": True, "data": context})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{meeting_id}/summary")
async def generate_meeting_summary(meeting_id: str):
    """
    Generate a post-call summary for a completed meeting.
    
    This endpoint uses OpenAI to analyze the transcript and
    generate action items, key points, and follow-up messages.
    """
    try:
        summary = await meeting_service.generate_summary(meeting_id)
        return ORJSONResponse(content={"success": True, "data": summary})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{meeting_id}/summary")
async def get_meeting_summary(meeting_id: str):
    """
    Get the generated summary for a meeting.
    """
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        summary_data = {
            "summary": meeting.get("summary"),
            "keyPoints": meeting.get("key_discussion_points", []),
            "actionItems": meeting.get("action_items", []),
            "nextSteps": meeting.get("next_steps", []),
        }
        return ORJSONResponse(content={"success": True, "data": summary_data})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ WebSocket ============

@ws_router.websocket("/ws/meetings/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str):
    """
    WebSocket endpoint for live meeting transcription and insights.
    
    Protocol:
    - Send binary audio chunks for transcription
    - Receive JSON messages with transcripts and insights
    - Send JSON commands: mark_moment, pin_insight, add_action_item, end_meeting
    """
    await meeting_websocket_endpoint(websocket, meeting_id)

