import { useEffect, useState } from 'react';
import { useCampaignWizard, type Contact } from './NewCampaignWizard';
import {
  useEnrichApolloContactListMutation,
  useUpdateApolloContactEnrichmentStatusMutation,
  useAiContactQualificationMutation,
  useContactQualificationProgressQuery,
  // Optimized APIs - minimal data, less memory
  useGetContactListMinimalQuery,
  useGetCampaignStatusMinimalQuery,
  type ContactMinimal,
} from '../../store';
import { skipToken } from '@reduxjs/toolkit/query';

// Pagination config - 10 contacts per page
const PAGE_SIZE = 10;

// Check if campaign has already completed contact qualification based on prospecting_cycle.status
// Step is completed if status has moved past contact_qualification_* to contact_enriched or later
const isStepAlreadyCompleted = (cycleStatus?: string): boolean => {
  const completedStatuses = [
    'contact_enriched',
    'hubspot_sync_in_progress',
    'hubspot_sync_completed',
    'hubspot_sync_failed',
    'personalization_completed',
    'enrolled_to_sequence',
  ];
  return cycleStatus ? completedStatuses.includes(cycleStatus) : false;
};

// Check if we should show mode selection (status is contact_qualification_select)
const shouldShowModeSelection = (cycleStatus?: string): boolean => {
  return cycleStatus === 'contact_qualification_select';
};

// Check if AI is actively running (status is contact_qualification_ai_started)
const isAiInProgress = (cycleStatus?: string): boolean => {
  return cycleStatus === 'contact_qualification_ai_started';
};

export const Step3ContactQualification = () => {
  const { 
    state, 
    setContactQualificationMode, 
    nextStep, 
    prevStep,
    setLoading,
  } = useCampaignWizard();

  const campaignId = state.campaignId;
  const [isEnrichPolling, setIsEnrichPolling] = useState(false);
  const [isWaitingForEnrichment, setIsWaitingForEnrichment] = useState(false); // true when user clicked Continue
  const [enrichApolloContactList] = useEnrichApolloContactListMutation();
  const [updateApolloContactEnrichmentStatus] = useUpdateApolloContactEnrichmentStatusMutation();
  
  // Pagination state - 10 items per page
  const [currentPage, setCurrentPage] = useState(1);
  
  // Track selections/deselections for CURRENT PAGE ONLY
  // pageSelectedIds: contacts newly selected on this page (not yet saved)
  // pageDeselectedIds: contacts that WERE is_relevant but user wants to deselect
  const [pageSelectedIds, setPageSelectedIds] = useState<Set<string>>(new Set());
  const [pageDeselectedIds, setPageDeselectedIds] = useState<Set<string>>(new Set());
  const [isSavingPage, setIsSavingPage] = useState(false);
  
  // AI Contact Qualification
  const [aiContactQualification] = useAiContactQualificationMutation();
  const [aiStopPolling, setAiStopPolling] = useState(false);
  const [isAiContinueLoading, setIsAiContinueLoading] = useState(false);
  
  // ALWAYS fetch AI job progress on mount (for resume support), then poll if AI mode is active
  // This ensures we detect in-progress/completed AI jobs when resuming a campaign
  const shouldPollAiProgress = Boolean(campaignId && state.contactQualificationMode === 'ai' && !aiStopPolling);
  const { data: aiProgressData } = useContactQualificationProgressQuery(
    campaignId ? { campaign_id: campaignId } : skipToken,
    {
      // Always fetch once (for resume), then poll only if AI mode is active
      pollingInterval: shouldPollAiProgress ? 3000 : 0,
    }
  );

  // OPTIMIZED: Use minimal contact list API with pagination
  // Only fetches 10 contacts at a time - no data accumulation
  const aiStatus = aiProgressData?.data?.status;
  const shouldPollContactList = Boolean(
    campaignId && 
    state.contactQualificationMode === 'ai' && 
    (aiStatus === 'running' || aiStatus === 'queued')
  );
  const { data: contactListData, refetch: refetchContactList } = useGetContactListMinimalQuery(
    campaignId ? { campaign_id: campaignId, page: currentPage, limit: PAGE_SIZE } : skipToken,
    { pollingInterval: shouldPollContactList ? 5000 : 0 }
  );
  
  // OPTIMIZED: Use minimal status API for polling - no contact data
  // Poll during enrichment OR when AI qualification is running (to get updated relevant_contacts count)
  const { data: statusData, refetch: refetchStatus } = useGetCampaignStatusMinimalQuery(
    campaignId ? { campaign_id: campaignId } : skipToken,
    { pollingInterval: 0 }
  );

  // Stop polling once AI job reaches terminal state and refetch contact list + status
  useEffect(() => {
    const status = aiProgressData?.data?.status;
    if (status === 'completed' || status === 'failed') {
      setAiStopPolling(true);
      // Refetch contact list to get updated is_relevant values
      refetchContactList();
      // Refetch status to get updated overall counts (relevant_contacts)
      refetchStatus();
    }
  }, [aiProgressData?.data?.status, refetchContactList, refetchStatus]);

  // Refetch contact list when mode is selected (fixes timing issue where initial fetch returned empty)
  useEffect(() => {
    if (state.contactQualificationMode && campaignId) {
      console.log('[Step3] Mode selected, refetching contact list');
      refetchContactList();
      refetchStatus();
    }
  }, [state.contactQualificationMode, campaignId, refetchContactList, refetchStatus]);
  
  // Use status from optimized status API (preferred) or contact list
  // statusData = { success, data: { status, ... } } from GetCampaignStatusMinimalResponse
  const statusFromMinimal = statusData?.data?.status;
  const cycleFromMinimal = statusData?.data?.prospecting_cycle?.status;
  const campaignCycleStatus =
    cycleFromMinimal ||
    statusFromMinimal ||
    contactListData?.data?.campaign_status?.prospecting_cycle?.status;
  const isEnrichmentInProgress =
    statusFromMinimal === 'contact_enrichment_in_progress' ||
    cycleFromMinimal === 'contact_enrichment_in_progress' ||
    campaignCycleStatus === 'contact_enrichment_in_progress';

  // Step is "already completed" if campaign has moved past contact qualification
  const stepAlreadyCompleted = isStepAlreadyCompleted(campaignCycleStatus);
  const isReviewOnly = stepAlreadyCompleted;
  const effectiveMode = isReviewOnly ? 'manual' : state.contactQualificationMode;
  
  // Enable status polling when enrichment is running or AI qualification is active.
  const shouldPollStatus =
    !stepAlreadyCompleted &&
    (isEnrichPolling ||
      isEnrichmentInProgress ||
      (shouldPollAiProgress && !aiStopPolling));
  useEffect(() => {
    if (!shouldPollStatus) return;
    const interval = setInterval(() => {
      refetchStatus();
    }, 3000);
    return () => clearInterval(interval);
  }, [shouldPollStatus, refetchStatus]);
  
  // Check if AI contact qualification has active/completed job
  const contactAiJobStatus = aiProgressData?.data?.status;
  
  // Derive state from backend status (source of truth)
  const showModeSelection =
    shouldShowModeSelection(campaignCycleStatus) &&
    !state.contactQualificationMode &&
    !stepAlreadyCompleted;
  const aiActiveFromStatus = isAiInProgress(campaignCycleStatus);
  
  // Log for debugging
  console.log('[Step3] cycleStatus:', campaignCycleStatus, 'mode:', state.contactQualificationMode, 
    'showModeSelection:', showModeSelection, 'aiActiveFromStatus:', aiActiveFromStatus, 
    'stepAlreadyCompleted:', stepAlreadyCompleted, 'aiJobStatus:', contactAiJobStatus);

  // Review-only: ensure we don't keep loading overlays running.
  useEffect(() => {
    if (stepAlreadyCompleted && state.isLoading) {
      setLoading(false);
    }
  }, [stepAlreadyCompleted, state.isLoading, setLoading]);

  // Review-only: stop any polling/enrichment state.
  useEffect(() => {
    if (!stepAlreadyCompleted) return;
    setAiStopPolling(true);
    setIsEnrichPolling(false);
    setIsWaitingForEnrichment(false);
  }, [stepAlreadyCompleted]);

  // Resume enrichment progress if backend is already enriching contacts.
  useEffect(() => {
    if (!campaignId || !isEnrichmentInProgress) return;
    if (!isWaitingForEnrichment) {
      setIsWaitingForEnrichment(true);
    }
    if (!isEnrichPolling) {
      setIsEnrichPolling(true);
    }
    if (!state.isLoading) {
      setLoading(true, 'Enriching contacts from Apollo...');
    }
  }, [
    campaignId,
    isEnrichmentInProgress,
    isWaitingForEnrichment,
    isEnrichPolling,
    setLoading,
    state.isLoading,
  ]);

  // AUTO-DETECT MODE based on backend status - ONLY when resuming a campaign
  // When status is contact_qualification_select, user MUST choose mode (don't auto-set)
  useEffect(() => {
    if (!campaignId) return;
    if (stepAlreadyCompleted) return;
    
    // IMPORTANT: When status is contact_qualification_select, user should choose mode
    // Don't auto-set any mode - let them see the mode selection
    if (campaignCycleStatus === 'contact_qualification_select') {
      console.log('[Step3] Status is contact_qualification_select - waiting for user to choose mode');
      return; // Exit early - don't auto-detect
    }
    
    // If backend status indicates AI is actively running, set AI mode
    if (campaignCycleStatus === 'contact_qualification_ai_started' && !state.contactQualificationMode) {
      console.log('[Step3] Auto-detected AI in progress from status');
      setContactQualificationMode('ai');
      return;
    }
    
    // If backend status is contact_qualification and AI job completed, set AI mode for review
    if (campaignCycleStatus === 'contact_qualification' && contactAiJobStatus === 'completed' && !state.contactQualificationMode) {
      console.log('[Step3] Auto-detected completed AI job for review');
      setContactQualificationMode('ai');
      setAiStopPolling(true);
      return;
    }
    
    // Fallback: only check AI job status when NOT in mode selection state
    if (!state.contactQualificationMode && contactAiJobStatus && contactAiJobStatus !== 'not_started' &&
        campaignCycleStatus !== 'contact_qualification_select') {
      console.log('[Step3] Auto-detected AI mode from job status:', contactAiJobStatus);
      setContactQualificationMode('ai');
      
      if (contactAiJobStatus === 'completed' || contactAiJobStatus === 'failed') {
        setAiStopPolling(true);
      }
    }
  }, [campaignId, campaignCycleStatus, contactAiJobStatus, state.contactQualificationMode, setContactQualificationMode, stepAlreadyCompleted]);
  
  // OPTIMIZED: Contacts from minimal API - only current page, not all
  const apiContacts: ContactMinimal[] = contactListData?.data?.contacts || [];
  // Use total_records from pagination (consistent with backend pagination structure)
  const totalContacts = contactListData?.pagination?.total_records || contactListData?.data?.total_count || 0;
  const totalPages = Math.ceil(totalContacts / PAGE_SIZE);

  // Auto-start polling if contacts are being fetched
  // This handles the Single Company flow where get_apollo_contact_list was queued before entering this step
  // Poll UNTIL status becomes 'contact_qualification_select' (ready for mode selection)
  useEffect(() => {
    if (!campaignId) return;
    
    // Get status directly from statusData to ensure fresh value
    const currentStatus = statusData?.data?.status;
    
    console.log('[Step3 Enrich Effect] currentStatus:', currentStatus, 'isEnrichPolling:', isEnrichPolling, 'contacts:', apiContacts.length);
    
    if (currentStatus === 'contact_enrichment_in_progress') {
      if (!isEnrichPolling || !isWaitingForEnrichment) {
        setLoading(true, 'Enriching contacts from Apollo...');
        setIsWaitingForEnrichment(true);
        setIsEnrichPolling(true);
      }
      return;
    }

    // STOP condition: status is contact_qualification_select - ready for mode selection
    if (currentStatus === 'contact_qualification_select') {
      if (isEnrichPolling) {
        console.log('[Step3] Status is contact_qualification_select, stopping enrich polling');
        setLoading(false);
        setIsEnrichPolling(false);
      }
      return;
    }
    
    // START condition: status is NOT contact_qualification_select and we have no contacts
    // This means contacts are still being fetched from Apollo
    if (!isEnrichPolling && apiContacts.length === 0 && currentStatus !== undefined) {
      console.log('[Step3] Starting enrich polling, current status:', currentStatus);
      setLoading(true, 'Fetching contacts from Apollo...');
      setIsEnrichPolling(true);
    }
  }, [campaignId, statusData?.data?.status, apiContacts.length, isEnrichPolling, setLoading, stepAlreadyCompleted]);

  // Map minimal contact data to display format - no state storage needed
  // Contact is qualified if:
  //   - Newly selected on this page (in pageSelectedIds), OR
  //   - Already is_relevant in DB AND not deselected on this page
  const displayContacts = apiContacts.map((c): Contact => {
    const isNewlySelected = pageSelectedIds.has(c.contact_id);
    const isDeselected = pageDeselectedIds.has(c.contact_id);
    const isQualified = isNewlySelected || (c.is_relevant && !isDeselected);
    
    return {
      id: c.contact_id,
      companyId: c.company_id,
      companyName: c.company || undefined,
      firstName: c.firstname || '',
      lastName: c.lastname || '',
      email: c.email || '',
      phone: c.phone || undefined,
      jobTitle: c.jobtitle || '',
      linkedinUrl: c.linkedin_url || undefined,
      qualificationStatus: isQualified ? 'qualified' : 'pending',
      syncStatus: 'not_synced',
      personalization: {
        messageStatus: 'pending',
        deckStatus: 'pending',
      },
    };
  });

  // Use displayContacts for rendering - no state accumulation
  const contacts = displayContacts;
  
  // Count for current page only (for "Select All" checkbox state)
  const currentPageQualifiedCount = apiContacts.filter(c => c.is_relevant || pageSelectedIds.has(c.contact_id)).length;
  
  // OVERALL COUNTS from backend (across ALL pages)
  const overallTotalContacts = statusData?.data?.total_contacts || totalContacts;
  const overallSelectedContacts = statusData?.data?.relevant_contacts || 0;

  // Get company name for a contact (prefer API-provided name)
  const getCompanyName = (contact: Contact) => {
    if (contact.companyName) return contact.companyName;
    return 'Unknown Company';
  };

  // Toggle single contact qualification via checkbox (current page only)
  const toggleContactQualification = (contactId: string) => {
    if (stepAlreadyCompleted) return;
    const contact = apiContacts.find(c => c.contact_id === contactId);
    if (!contact) return;
    
    const isCurrentlyQualified = pageSelectedIds.has(contactId) || (contact.is_relevant && !pageDeselectedIds.has(contactId));
    
    if (isCurrentlyQualified) {
      // DESELECT: Remove from pageSelectedIds, add to pageDeselectedIds if was is_relevant
      setPageSelectedIds(prev => {
        const next = new Set(prev);
        next.delete(contactId);
        return next;
      });
      if (contact.is_relevant) {
        setPageDeselectedIds(prev => new Set(prev).add(contactId));
      }
    } else {
      // SELECT: Add to pageSelectedIds, remove from pageDeselectedIds
      setPageSelectedIds(prev => new Set(prev).add(contactId));
      setPageDeselectedIds(prev => {
        const next = new Set(prev);
        next.delete(contactId);
        return next;
      });
    }
  };

  // Select/Deselect all contacts on current page
  const handleSelectAll = () => {
    if (stepAlreadyCompleted) return;
    const allQualified = displayContacts.every(c => c.qualificationStatus === 'qualified');
    if (allQualified) {
      // Deselect all on this page
      setPageSelectedIds(new Set());
      // Mark all is_relevant contacts as deselected
      setPageDeselectedIds(new Set(apiContacts.filter(c => c.is_relevant).map(c => c.contact_id)));
    } else {
      // Select all on this page
      setPageSelectedIds(new Set(displayContacts.map(c => c.id)));
      setPageDeselectedIds(new Set());
    }
  };

  // Save current page selections AND deselections to backend before changing page
  const saveCurrentPageSelections = async (): Promise<boolean> => {
    if (!campaignId) return true;
    
    // NEW selections on this page (not already is_relevant in DB)
    const newSelectionsOnThisPage = apiContacts
      .filter(c => pageSelectedIds.has(c.contact_id) && !c.is_relevant)
      .map(c => c.contact_id);
    
    // DESELECTIONS on this page (were is_relevant, now deselected)
    const deselectedOnThisPage = Array.from(pageDeselectedIds);
    
    // If no changes, nothing to save
    if (newSelectionsOnThisPage.length === 0 && deselectedOnThisPage.length === 0) {
      return true;
    }
    
    setIsSavingPage(true);
    try {
      // Save selected contacts (is_relevant = true)
      if (newSelectionsOnThisPage.length > 0) {
        await updateApolloContactEnrichmentStatus({
          campaign_id: campaignId,
          selection_type: 'selected',
          is_relevant: true,
          contact_ids: newSelectionsOnThisPage,
        }).unwrap();
      }
      
      // Save deselected contacts (is_relevant = false)
      if (deselectedOnThisPage.length > 0) {
        await updateApolloContactEnrichmentStatus({
          campaign_id: campaignId,
          selection_type: 'selected',
          is_relevant: false,
          contact_ids: deselectedOnThisPage,
        }).unwrap();
      }
      
      // Refetch status to update overall counts
      refetchStatus();
      
      return true;
    } catch (e) {
      console.error('Failed to save page selections:', e);
      return false;
    } finally {
      setIsSavingPage(false);
    }
  };

  // Handle page change - save current page first, then change page
  const handlePageChange = async (newPage: number) => {
    if (newPage === currentPage || isSavingPage) return;
    
    if (stepAlreadyCompleted) {
      setCurrentPage(newPage);
      return;
    }
    
    // Save current page selections/deselections before navigating
    const saved = await saveCurrentPageSelections();
    if (saved) {
      // Clear page-specific state (they're now saved to DB)
      setPageSelectedIds(new Set());
      setPageDeselectedIds(new Set());
      setCurrentPage(newPage);
    }
  };

  const allSelected = displayContacts.length > 0 && displayContacts.every(c => c.qualificationStatus === 'qualified');
  const someSelected = displayContacts.some(c => c.qualificationStatus === 'qualified') && !allSelected;

  const handleContinue = () => {
    // Before going to Step 4, save current page, then queue contact enrichment
    if (!campaignId) {
      nextStep();
      return;
    }

    if (isWaitingForEnrichment || isEnrichmentInProgress || stepAlreadyCompleted) {
      return;
    }

    // Calculate effective selected count after pending changes
    const effectiveSelectedCount = overallSelectedContacts 
      + apiContacts.filter(c => pageSelectedIds.has(c.contact_id) && !c.is_relevant).length
      - pageDeselectedIds.size;
    
    if (effectiveSelectedCount <= 0) {
      // nothing selected anywhere; don't start enrichment chain
      return;
    }

    setLoading(true, 'Saving selected contacts…');
    void (async () => {
      try {
        // 1) Save current page selections first (NEW selections only)
        const newSelectionsOnThisPage = apiContacts
          .filter(c => pageSelectedIds.has(c.contact_id) && !c.is_relevant)
          .map(c => c.contact_id);
        
        if (newSelectionsOnThisPage.length > 0) {
          await updateApolloContactEnrichmentStatus({
            campaign_id: campaignId,
            selection_type: 'selected',
            is_relevant: true,
            contact_ids: newSelectionsOnThisPage,
          }).unwrap();
        }
        
        // 2) Save deselections (is_relevant = false)
        if (pageDeselectedIds.size > 0) {
          await updateApolloContactEnrichmentStatus({
            campaign_id: campaignId,
            selection_type: 'selected',
            is_relevant: false,
            contact_ids: Array.from(pageDeselectedIds),
          }).unwrap();
        }

        // 3) Queue enrichment job - backend will enrich all is_relevant contacts
        await enrichApolloContactList({ campaign_id: campaignId, enrichment_status: true }).unwrap();
        setLoading(true, 'Enriching contacts from Apollo…');
        // 4) Start polling for contact_enriched
        setIsWaitingForEnrichment(true); // Mark that we're waiting for enrichment, not initial fetch
        setIsEnrichPolling(true);
      } catch (e) {
        setLoading(false);
        setIsEnrichPolling(false);
        setIsWaitingForEnrichment(false);
      }
    })();
  };

  // Handler for AI qualification flow - uses apiContacts instead of state contacts
  const handleAiContinue = () => {
    if (!campaignId) {
      nextStep();
      return;
    }

    if (isWaitingForEnrichment || isEnrichmentInProgress || stepAlreadyCompleted) {
      return;
    }

    // Get relevant contact IDs from API contacts (AI-qualified)
    const relevantContactIds = apiContacts
      .filter((c) => c.is_relevant)
      .map((c) => c.contact_id);

    if (relevantContactIds.length === 0) {
      return;
    }

    setIsAiContinueLoading(true);
    setLoading(true, 'Saving selected contacts…');
    void (async () => {
      try {
        // 1) Persist selected contact ids (is_relevant=true) - same as manual flow
        await updateApolloContactEnrichmentStatus({
          campaign_id: campaignId,
          selection_type: 'selected',
          is_relevant: true,
          contact_ids: relevantContactIds,
        }).unwrap();

        // 2) Queue enrichment job
        await enrichApolloContactList({ campaign_id: campaignId, enrichment_status: true }).unwrap();
        setLoading(true, 'Enriching contacts from Apollo…');
        
        // 3) Start polling for contact_enriched
        setIsWaitingForEnrichment(true);
        setIsEnrichPolling(true);
      } catch (e) {
        setLoading(false);
        setIsEnrichPolling(false);
        setIsWaitingForEnrichment(false);
        setIsAiContinueLoading(false);
      }
    })();
  };

  // OPTIMIZED: Watch status via minimal API - when enriched, just proceed to next step
  // No more fetching ALL contacts and storing in wizard state!
  useEffect(() => {
    if (!campaignId || !isEnrichPolling) return;
    
    // Use data.status (main status field) - this is the source of truth
    const status = statusData?.data?.status;
    
    console.log('[Step3 Watch Effect] status:', status, 'isEnrichPolling:', isEnrichPolling, 'isWaitingForEnrichment:', isWaitingForEnrichment);
    
    // STOP condition: status reaches 'contact_qualification_select'
    const isReadyForModeSelection = status === 'contact_qualification_select';
    const isContactsEnriched = status === 'contact_enriched';
    
    // If we're waiting for enrichment (user clicked Continue), only proceed when enriched
    if (isWaitingForEnrichment) {
      if (isContactsEnriched) {
        setLoading(false);
        setIsEnrichPolling(false);
        setIsWaitingForEnrichment(false);
        // Don't store contacts - Step 4 will fetch its own paginated data
        nextStep();
      }
    } else {
      // Initial display - stop polling when status reaches contact_qualification_select
      if (isReadyForModeSelection) {
        console.log('[Step3] Status reached contact_qualification_select, stopping enrich polling');
        setLoading(false);
        setIsEnrichPolling(false);
        // Stay on this page for user to qualify - data displayed via useGetContactListMinimalQuery
      }
    }
  }, [campaignId, isEnrichPolling, isWaitingForEnrichment, statusData?.data?.status, nextStep, setLoading]);

  return (
    <div className="step-container step-contact-qualification">
      <div className="step-header">
        <h2>Contact Qualification</h2>
        <p>Review and qualify contacts from your qualified companies</p>
      </div>

      {/* Loading Animation - Only show when NOT in AI mode or before AI starts */}
      {state.isLoading && effectiveMode !== 'ai' && !isReviewOnly && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-animation ai-animation">
              <div className="ai-brain">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <div className="ai-pulse" />
            </div>
            <h3>{state.loadingMessage}</h3>
            <div className="loading-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill ai-progress" 
                  style={{ width: `${state.estimatedCount}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode Selection - Show only if step not already completed, mode not selected, and status is contact_qualification_select */}
      {(showModeSelection || (!state.contactQualificationMode && !stepAlreadyCompleted && !aiActiveFromStatus && !isEnrichmentInProgress)) && (
        <div className="qualification-mode-selection">
          <h3>Choose Qualification Method</h3>
          <div className="mode-cards">
            <div 
              className="mode-card"
              onClick={() => setContactQualificationMode('manual')}
            >
              <div className="mode-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h4>Manual Qualification</h4>
              <p>Review each contact individually and decide if they qualify</p>
              <span className="mode-tag">Full Control</span>
            </div>
            <div 
              className="mode-card"
              onClick={() => setContactQualificationMode('ai')}
            >
              <div className="mode-icon ai">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4c0 1.1-.9 2-2 2h-4c-1.1 0-2-.9-2-2a4 4 0 0 1 4-4z"/>
                  <path d="M12 8v8"/>
                  <path d="M5 12h14"/>
                  <circle cx="5" cy="12" r="2"/>
                  <circle cx="19" cy="12" r="2"/>
                  <circle cx="12" cy="19" r="2"/>
                </svg>
              </div>
              <h4>AI Qualification</h4>
              <p>Let AI qualify contacts based on criteria</p>
              <span className="mode-tag ai">AI Powered</span>
            </div>
          </div>
        </div>
      )}

      {/* Manual Qualification */}
      {effectiveMode === 'manual' && (
        <div className="manual-qualification">
          {isReviewOnly && (
            <div className="sync-success-banner" style={{ marginBottom: '24px' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <span>Contact Qualification Completed (view only)</span>
            </div>
          )}
          {/* Stats Bar - OVERALL counts across all pages */}
          <div className="qualification-stats">
            <div className="stat">
              <span className="stat-value">{overallTotalContacts}</span>
              <span className="stat-label">TOTAL</span>
            </div>
            <div className="stat qualified">
              <span className="stat-value">
                {/* Overall selected = backend count + NEW selections - DESELECTIONS on this page */}
                {Math.max(0, 
                  overallSelectedContacts 
                  + apiContacts.filter(c => pageSelectedIds.has(c.contact_id) && !c.is_relevant).length
                  - pageDeselectedIds.size
                )}
              </span>
              <span className="stat-label">SELECTED</span>
            </div>
          </div>

          {/* Contacts List with Select All Header */}
          <div className="contacts-qualification-list">
            {/* Select All Header */}
            <div className="select-all-header">
              <label className="checkbox-container">
                <input 
                  type="checkbox" 
                  checked={allSelected}
                  ref={(el) => {
                    if (el) el.indeterminate = someSelected;
                  }}
                  onChange={handleSelectAll}
                  disabled={stepAlreadyCompleted}
                />
                <span className="checkmark"></span>
              </label>
              <span className="select-all-text">
                {stepAlreadyCompleted
                  ? 'Selected Contacts (view only)'
                  : allSelected
                    ? 'Deselect All'
                    : 'Select All'}
                <span className="selected-count">({currentPageQualifiedCount} of {contacts.length} selected)</span>
              </span>
            </div>

            {/* Contacts */}
            {contacts.map((contact) => {
              const isQualified = contact.qualificationStatus === 'qualified';
              return (
                <div 
                  key={contact.id} 
                  className={`contact-qualification-card ${isQualified ? 'qualified' : ''}`}
                  onClick={() => {
                    if (!stepAlreadyCompleted) {
                      toggleContactQualification(contact.id);
                    }
                  }}
                >
                  <div className="contact-select">
                    <label className="checkbox-container">
                      <input 
                        type="checkbox"
                        checked={isQualified}
                        onChange={() => toggleContactQualification(contact.id)}
                        onClick={(e) => e.stopPropagation()}
                        disabled={stepAlreadyCompleted}
                      />
                      <span className="checkmark"></span>
                    </label>
                  </div>
                  <div className="contact-avatar">
                    {contact.firstName[0]}{contact.lastName[0]}
                  </div>
                  <div className="contact-info">
                    <h4>{contact.firstName} {contact.lastName}</h4>
                    <div className="contact-meta">
                      <span className="job-title">{contact.jobTitle}</span>
                      <span className="company-name">{getCompanyName(contact)}</span>
                    </div>
                    <span className="contact-email">{contact.email || 'No email found'}</span>
                  </div>
                  {isQualified && (
                    <div className="qualified-badge">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    </div>
                  )}
                </div>
              );
            })}
            
            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="pagination-controls" style={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                gap: '16px', 
                padding: '16px',
                marginTop: '16px',
                borderTop: '1px solid var(--color-gray-200)'
              }}>
                <button 
                  className="btn-secondary"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1 || isSavingPage}
                  style={{ minWidth: '100px' }}
                >
                  {isSavingPage ? 'Saving...' : 'Previous'}
                </button>
                <span style={{ color: 'var(--color-gray-600)' }}>
                  Page {currentPage} of {totalPages} ({overallTotalContacts} contacts)
                </span>
                <button 
                  className="btn-secondary"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages || isSavingPage}
                  style={{ minWidth: '100px' }}
                >
                  {isSavingPage ? 'Saving...' : 'Next'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Qualification */}
      {effectiveMode === 'ai' && (
        <div className="manual-qualification">
          <div className="ai-qualification-setup">
            <div className="ai-setup-header">
              <h3>AI Contact Qualification</h3>
              <p>AI will qualify contacts based on campaign criteria.</p>
            </div>

            {/* Show progress if AI job is running */}
            {aiProgressData?.data && aiProgressData.data.status !== 'not_started' ? (
              <div className="sync-progress-container" style={{ marginTop: 24 }}>
                <div className="sync-progress-header">
                  <span className="sync-progress-status">
                    {(aiProgressData.data.status === 'queued' || aiProgressData.data.status === 'running') && (
                      <div className="spinner small" />
                    )}
                    {aiProgressData.data.status === 'completed' ? (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                      </svg>
                    ) : null}
                    {aiProgressData.data.status === 'queued' && 'Starting AI qualification...'}
                    {aiProgressData.data.status === 'running' && 'AI is qualifying contacts...'}
                    {aiProgressData.data.status === 'completed' && 'AI qualification completed!'}
                    {aiProgressData.data.status === 'failed' && 'AI qualification failed'}
                  </span>
                  <span className="sync-progress-count">
                    {aiProgressData.data.progress.processed} / {aiProgressData.data.progress.total} contacts
                  </span>
                </div>
                <div className="sync-progress-bar">
                  <div 
                    className={`sync-progress-fill ${aiProgressData.data.progress.total > 0 && aiProgressData.data.progress.processed > 0 ? '' : 'sync-progress-indeterminate'}`}
                    style={{ 
                      width: aiProgressData.data.progress.total > 0 
                        ? `${Math.min(100, Math.round((aiProgressData.data.progress.processed / aiProgressData.data.progress.total) * 100))}%` 
                        : '0%' 
                    }}
                  />
                </div>
                
                {/* Stats below progress bar - show OVERALL counts from status API (updates after manual changes) */}
                <div className="qualification-stats" style={{ marginTop: 16 }}>
                  <div className="stat">
                    <span className="stat-value">{overallTotalContacts || aiProgressData.data.progress.total}</span>
                    <span className="stat-label">TOTAL</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{aiProgressData.data.progress.processed}</span>
                    <span className="stat-label">PROCESSED</span>
                  </div>
                  <div className="stat qualified">
                    <span className="stat-value">{overallSelectedContacts || aiProgressData.data.progress.relevant}</span>
                    <span className="stat-label">SELECTED</span>
                  </div>
                </div>

                {aiProgressData.data.error ? (
                  <div className="sync-error-banner" style={{ marginTop: 16 }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/>
                      <line x1="15" y1="9" x2="9" y2="15"/>
                      <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                    <span>{aiProgressData.data.error}</span>
                  </div>
                ) : null}

                {/* Show contacts list after AI qualification is completed or running */}
                {(aiProgressData.data.status === 'completed' || aiProgressData.data.status === 'running') && apiContacts.length > 0 && (
                  <div className="contacts-qualification-list" style={{ marginTop: 24 }}>
                    <div className="select-all-header">
                      <label className="checkbox-container">
                        <input 
                          type="checkbox" 
                          checked={apiContacts.length > 0 && apiContacts.every(c => c.is_relevant)}
                          ref={(el) => {
                            if (el) el.indeterminate = apiContacts.some(c => c.is_relevant) && !apiContacts.every(c => c.is_relevant);
                          }}
                          onChange={() => {
                            if (!campaignId) return;
                            const allSelected = apiContacts.every(c => c.is_relevant);
                            const allContactIds = apiContacts.map(c => c.contact_id);
                            void (async () => {
                              try {
                                await updateApolloContactEnrichmentStatus({
                                  campaign_id: campaignId,
                                  selection_type: 'selected',
                                  is_relevant: !allSelected,
                                  contact_ids: allContactIds,
                                  relevance_reason: !allSelected ? 'Manual selection (Select All)' : 'Manually marked as not relevant (Deselect All)',
                                }).unwrap();
                                refetchContactList();
                                refetchStatus(); // Update overall counts
                              } catch (e) {
                                console.error('Failed to update all contacts:', e);
                              }
                            })();
                          }}
                        />
                        <span className="checkmark"></span>
                      </label>
                      <span className="select-all-text">
                        {apiContacts.every(c => c.is_relevant) ? 'Deselect All' : 'Select All'}
                        <span className="selected-count">
                          ({apiContacts.filter(c => c.is_relevant).length} of {apiContacts.length} on this page)
                        </span>
                      </span>
                    </div>

                    {apiContacts.map((contact) => {
                      const isRelevant = contact.is_relevant;
                      const hasReason = !!contact.relevance_reason;
                      return (
                        <div 
                          key={contact.contact_id} 
                          className={`contact-qualification-card ${isRelevant ? 'qualified' : ''}`}
                          style={{ cursor: 'pointer' }}
                          onClick={() => {
                            if (!campaignId) return;
                            // Toggle relevance and update reason
                            void (async () => {
                              try {
                                await updateApolloContactEnrichmentStatus({
                                  campaign_id: campaignId,
                                  selection_type: 'selected',
                                  is_relevant: !isRelevant,
                                  contact_ids: [contact.contact_id],
                                  relevance_reason: !isRelevant ? 'Manual selection' : 'Manually marked as not relevant',
                                }).unwrap();
                                // Refetch contact list to show updated status
                                refetchContactList();
                                refetchStatus(); // Update overall counts
                              } catch (e) {
                                console.error('Failed to update contact relevance:', e);
                              }
                            })();
                          }}
                        >
                          <div className="contact-select">
                            <label className="checkbox-container">
                              <input 
                                type="checkbox"
                                checked={isRelevant}
                                onChange={() => {}}
                                onClick={(e) => e.stopPropagation()}
                              />
                              <span className="checkmark"></span>
                            </label>
                          </div>
                          <div className="contact-avatar">
                            {contact.firstname?.[0] || '?'}{contact.lastname?.[0] || '?'}
                          </div>
                          <div className="contact-info" style={{ flex: 1 }}>
                            <h4>{contact.firstname || ''} {contact.lastname || ''}</h4>
                            <div className="contact-meta">
                              <span className="job-title">{contact.jobtitle || 'N/A'}</span>
                              <span className="company-name">{contact.company || 'Unknown'}</span>
                            </div>
                            <span className="contact-email">{contact.email || 'No email'}</span>
                            {hasReason && (
                              <div style={{ 
                                marginTop: 8, 
                                fontSize: 12, 
                                color: isRelevant ? '#059669' : '#dc2626',
                                background: isRelevant ? '#ecfdf5' : '#fef2f2',
                                padding: '6px 10px',
                                borderRadius: 6,
                                lineHeight: 1.4,
                              }}>
                                <strong>{isRelevant ? '✓ Relevant:' : '✗ Not Relevant:'}</strong> {contact.relevance_reason}
                              </div>
                            )}
                          </div>
                          {isRelevant ? (
                            <div className="qualified-badge">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="20 6 9 17 4 12"/>
                              </svg>
                            </div>
                          ) : (
                            <div style={{ 
                              width: 28, height: 28, borderRadius: '50%', 
                              background: '#fef2f2', display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                              </svg>
                            </div>
                          )}
                        </div>
                      );
                    })}
                    
                    {/* Pagination Controls for AI Mode */}
                    {totalPages > 1 && (
                      <div className="pagination-controls" style={{ 
                        display: 'flex', 
                        justifyContent: 'center', 
                        alignItems: 'center', 
                        gap: '16px', 
                        padding: '16px',
                        marginTop: '16px',
                        borderTop: '1px solid var(--color-gray-200)'
                      }}>
                        <button 
                          className="btn-secondary"
                          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                          style={{ minWidth: '100px' }}
                        >
                          Previous
                        </button>
                        <span style={{ color: 'var(--color-gray-600)' }}>
                          Page {currentPage} of {totalPages} ({overallTotalContacts} contacts)
                        </span>
                        <button 
                          className="btn-secondary"
                          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                          style={{ minWidth: '100px' }}
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Continue button when completed - use overall relevant count */}
                {aiProgressData.data.status === 'completed' && (
                  <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end' }}>
                    <button 
                      className="btn-primary" 
                      onClick={handleAiContinue}
                      disabled={isAiContinueLoading || (overallSelectedContacts === 0) || isWaitingForEnrichment || isEnrichmentInProgress}
                      style={{ display: 'flex', alignItems: 'center', gap: 8 }}
                    >
                      {isAiContinueLoading || isWaitingForEnrichment || isEnrichmentInProgress ? (
                        <>
                          <div className="spinner small" style={{ width: 16, height: 16, borderWidth: 2 }} />
                          Enriching...
                        </>
                      ) : (
                        <>
                          Continue with {overallSelectedContacts} Contacts
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="5" y1="12" x2="19" y2="12"/>
                            <polyline points="12 5 19 12 12 19"/>
                          </svg>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="ai-setup-actions" style={{ marginTop: 24 }}>
                <button
                  className="btn-secondary"
                  onClick={() => setContactQualificationMode(null)}
                >
                  Back
                </button>
                <div style={{ flex: 1 }} />
                <button
                  className="btn-primary"
                  onClick={() => {
                    if (!campaignId) return;
                    void (async () => {
                      try {
                        await aiContactQualification({ campaign_id: campaignId }).unwrap();
                        setAiStopPolling(false); // Enable polling
                      } catch (e) {
                        console.error('Failed to start AI qualification:', e);
                      }
                    })();
                  }}
                >
                  Start AI Qualification
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Navigation - only show when step is NOT already completed */}
      {!stepAlreadyCompleted && (
        <div className="step-navigation">
          <button className="btn-secondary" onClick={() => {
            setContactQualificationMode(null);
            prevStep();
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back
          </button>
          
          {state.contactQualificationMode && (
            <button className="btn-secondary" onClick={() => {
              setContactQualificationMode(null);
            }}>
              Change Method
            </button>
          )}

          {state.contactQualificationMode !== 'ai' && (isWaitingForEnrichment || isEnrichmentInProgress) && (
            <button className="btn-primary btn-large" disabled>
              <div className="spinner small" style={{ width: 16, height: 16, borderWidth: 2, marginRight: 8 }} />
              Enriching contacts...
            </button>
          )}

          {(overallSelectedContacts > 0 || pageSelectedIds.size > 0) &&
            state.contactQualificationMode !== 'ai' &&
            !isWaitingForEnrichment &&
            !isEnrichmentInProgress && (
              <button className="btn-primary btn-large" onClick={handleContinue}>
                Continue with {Math.max(0, overallSelectedContacts + apiContacts.filter(c => pageSelectedIds.has(c.contact_id) && !c.is_relevant).length - pageDeselectedIds.size)} Contacts
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                  <polyline points="12 5 19 12 12 19"/>
                </svg>
              </button>
            )}
        </div>
      )}
    </div>
  );
};
