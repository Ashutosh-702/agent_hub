import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { CompanyDraft, CompanyEnrichment, HubSpotCompany } from '../../types/hubspot';
import {
  canonicalizeDomain,
  searchHubspotCompanies,
  enrichCompany,
  createHubspotCompany,
  linkExistingCompany,
} from '../../services/mockHubspot';
import { Button, Input, Stepper, Card, Badge, JsonViewer, RadioGroup } from './ui';
import { useToast } from './ui/Toast';
import { ConfidenceBadge } from './ui/Badge';

type Step = 'input' | 'match' | 'enrich' | 'review' | 'done';

// Fields that can be edited in review step
type EditableField = 'companyName' | 'legalEntityName' | 'industry' | 'employeeBand' | 'hqLocation' | 'website';

const STEPS = [
  { id: 'input', title: 'Input' },
  { id: 'match', title: 'Match' },
  { id: 'enrich', title: 'Enrich' },
  { id: 'review', title: 'Review' },
  { id: 'done', title: 'Done' },
];

const initialDraft: CompanyDraft = {
  url: '',
  canonicalDomain: '',
  ownerEmail: '',
};

// Pencil Icon component
const PencilIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
    <path d="m15 5 4 4" />
  </svg>
);

// Check Icon component
const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

export const CreateCompanyWizard = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState<Step>('input');
  const [draft, setDraft] = useState<CompanyDraft>(initialDraft);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HubSpotCompany | null>(null);
  const [editableEnrichment, setEditableEnrichment] = useState<CompanyEnrichment | null>(null);
  const [editingFields, setEditingFields] = useState<Set<EditableField>>(new Set());

  const completedSteps = STEPS.slice(0, STEPS.findIndex(s => s.id === currentStep)).map(s => s.id);

  const updateDraft = useCallback((updates: Partial<CompanyDraft>) => {
    setDraft(prev => ({ ...prev, ...updates }));
  }, []);

  // Toggle edit mode for a specific field
  const toggleEditField = (field: EditableField) => {
    setEditingFields(prev => {
      const next = new Set(prev);
      if (next.has(field)) {
        next.delete(field);
      } else {
        next.add(field);
      }
      return next;
    });
  };

  // Check if a field is being edited
  const isEditing = (field: EditableField) => editingFields.has(field);

  // Step 1: Input
  const handleInputSubmit = async () => {
    if (!draft.url || !draft.ownerEmail) {
      setError('Please fill in all required fields');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const domain = await canonicalizeDomain(draft.url);
      updateDraft({ canonicalDomain: domain });

      const matches = await searchHubspotCompanies({ domain });
      updateDraft({ matchResults: matches });

      // Default to link if exact match found
      if (matches.length > 0) {
        const exactMatch = matches.find(m => m.domain === domain);
        if (exactMatch) {
          updateDraft({
            decision: 'link',
            selectedExistingCompanyId: exactMatch.id,
          });
        }
      } else {
        updateDraft({ decision: 'create' });
      }

      setCurrentStep('match');
    } catch (err) {
      setError('Failed to search for companies. Please try again.');
      showToast('Failed to search for companies', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Match
  const handleMatchContinue = () => {
    if (draft.decision === 'link' && !draft.selectedExistingCompanyId) {
      setError('Please select a company to link');
      return;
    }
    setError(null);
    setCurrentStep('enrich');
    handleEnrich();
  };

  // Step 3: Enrich
  const handleEnrich = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const enriched = await enrichCompany({
        url: draft.url,
        domain: draft.canonicalDomain,
      });
      updateDraft({ enriched });
      setEditableEnrichment({ ...enriched });
      setCurrentStep('review');
    } catch (err) {
      setError('Failed to enrich company data. Please try again.');
      showToast('Enrichment failed', 'error');
      setCurrentStep('review');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 4: Review & Create/Link
  const handleFinalSubmit = async () => {
    // Legal Entity Name should be auto-filled from enrichment
    // Only show error if it's somehow missing
    if (!editableEnrichment?.legalEntityName) {
      setError('Legal Entity Name is missing. Please click the edit button to add it.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setEditingFields(new Set()); // Clear all editing states

    try {
      let company: HubSpotCompany;

      if (draft.decision === 'link' && draft.selectedExistingCompanyId) {
        company = await linkExistingCompany(draft.selectedExistingCompanyId, {
          enrichedData: editableEnrichment,
        });
        showToast('Company linked successfully!', 'success');
      } else {
        company = await createHubspotCompany({
          name: editableEnrichment.companyName,
          domain: draft.canonicalDomain,
          legalEntityName: editableEnrichment.legalEntityName,
          ownerEmail: draft.ownerEmail,
          industry: editableEnrichment.industry,
          employeeBand: editableEnrichment.employeeBand,
          hqLocation: editableEnrichment.hqLocation,
          website: editableEnrichment.website,
          linkedIn: editableEnrichment.linkedIn,
        });
        showToast('Company created successfully!', 'success');
      }

      setResult(company);
      setCurrentStep('done');
    } catch (err) {
      setError('Failed to complete operation. Please try again.');
      showToast('Operation failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const goBack = () => {
    const stepOrder: Step[] = ['input', 'match', 'enrich', 'review', 'done'];
    const currentIndex = stepOrder.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(stepOrder[currentIndex - 1]);
    }
  };

  const resetWizard = () => {
    setDraft(initialDraft);
    setCurrentStep('input');
    setResult(null);
    setEditableEnrichment(null);
    setError(null);
    setEditingFields(new Set());
  };

  // Render Step Content
  const renderStepContent = () => {
    switch (currentStep) {
      case 'input':
        return (
          <Card padding="lg" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Enter Company Details
              </h2>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                We'll search HubSpot for existing matches first.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <Input
                label="Company URL"
                placeholder="https://example.com"
                value={draft.url}
                onChange={(e) => updateDraft({ url: e.target.value })}
                required
                hint="Enter the company's website URL"
              />
              <Input
                label="HubSpot Owner Email"
                type="email"
                placeholder="owner@yourcompany.com"
                value={draft.ownerEmail}
                onChange={(e) => updateDraft({ ownerEmail: e.target.value })}
                required
                hint="The HubSpot user who will own this company"
              />

              {error && (
                <div style={{
                  padding: '0.75rem 1rem',
                  background: 'rgba(220, 38, 38, 0.08)',
                  border: '1px solid rgba(220, 38, 38, 0.2)',
                  borderRadius: '8px',
                  color: 'var(--color-error)',
                  fontSize: '0.875rem',
                }}>
                  {error}
                </div>
              )}

              <Button
                onClick={handleInputSubmit}
                isLoading={isLoading}
                fullWidth
                size="lg"
                disabled={!draft.url || !draft.ownerEmail}
              >
                Search & Continue
              </Button>
            </div>
          </Card>
        );

      case 'match':
        return (
          <Card padding="lg" style={{ maxWidth: '700px', margin: '0 auto' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Match Results
              </h2>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Domain: <code style={{ background: 'var(--color-gray-100)', padding: '0.125rem 0.5rem', borderRadius: '4px' }}>{draft.canonicalDomain}</code>
              </p>
            </div>

            {draft.matchResults && draft.matchResults.length > 0 ? (
              <>
                <div style={{
                  padding: '0.75rem 1rem',
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  borderRadius: '8px',
                  marginBottom: '1.5rem',
                  fontSize: '0.875rem',
                  color: 'var(--color-success)',
                }}>
                  💡 We found {draft.matchResults.length} potential match{draft.matchResults.length > 1 ? 'es' : ''}. Linking prevents duplicates!
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-gray-700)' }}>
                    Existing Companies
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {draft.matchResults.map((company) => (
                      <label
                        key={company.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          padding: '1rem',
                          border: `2px solid ${draft.selectedExistingCompanyId === company.id ? 'var(--color-primary)' : 'var(--color-gray-200)'}`,
                          borderRadius: '8px',
                          cursor: 'pointer',
                          background: draft.selectedExistingCompanyId === company.id ? 'rgba(46, 49, 190, 0.04)' : 'var(--color-white)',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="radio"
                          name="existingCompany"
                          checked={draft.selectedExistingCompanyId === company.id}
                          onChange={() => updateDraft({ selectedExistingCompanyId: company.id, decision: 'link' })}
                          style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary)' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: 'var(--color-gray-900)' }}>{company.name}</div>
                          <div style={{ fontSize: '0.8125rem', color: 'var(--color-gray-500)' }}>
                            {company.domain} • {company.legalEntityName || 'No legal name'}
                          </div>
                        </div>
                        {company.domain === draft.canonicalDomain && (
                          <Badge variant="success">Exact Match</Badge>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div style={{
                padding: '1.5rem',
                background: 'var(--color-gray-50)',
                borderRadius: '8px',
                marginBottom: '1.5rem',
                textAlign: 'center',
              }}>
                <p style={{ margin: 0, color: 'var(--color-gray-500)' }}>
                  No existing companies found for this domain. A new company will be created.
                </p>
              </div>
            )}

            <RadioGroup
              name="decision"
              label="What would you like to do?"
              options={[
                {
                  value: 'link',
                  label: 'Link to Existing Company',
                  description: draft.matchResults?.length ? 'Connect to a company that already exists in HubSpot' : 'No matching companies found',
                },
                {
                  value: 'create',
                  label: 'Create New Company',
                  description: 'Add a brand new company record to HubSpot',
                },
              ]}
              value={draft.decision}
              onChange={(value) => updateDraft({ decision: value as 'link' | 'create' })}
            />

            {error && (
              <div style={{
                padding: '0.75rem 1rem',
                background: 'rgba(220, 38, 38, 0.08)',
                border: '1px solid rgba(220, 38, 38, 0.2)',
                borderRadius: '8px',
                color: 'var(--color-error)',
                fontSize: '0.875rem',
                marginTop: '1rem',
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
              <Button variant="secondary" onClick={goBack} style={{ flex: 1 }}>
                Back
              </Button>
              <Button onClick={handleMatchContinue} isLoading={isLoading} style={{ flex: 2 }}>
                Continue to Enrich
              </Button>
            </div>
          </Card>
        );

      case 'enrich':
        return (
          <Card padding="lg" style={{ maxWidth: '500px', margin: '0 auto', textAlign: 'center' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                margin: '0 auto 1.5rem',
                borderRadius: '50%',
                background: 'var(--color-primary-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  border: '3px solid var(--color-primary)',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                }}
              />
            </div>
            <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
              Enriching Company Data...
            </h2>
            <p style={{ margin: 0, color: 'var(--color-gray-500)', fontSize: '0.875rem' }}>
              We're fetching additional company information to populate HubSpot fields.
            </p>
          </Card>
        );

      case 'review':
        // Reusable review field component
        const ReviewField = ({
          field,
          label,
          value,
          confidence,
          type = 'text',
        }: {
          field: EditableField;
          label: string;
          value: string;
          confidence?: 'high' | 'medium' | 'low';
          type?: string;
        }) => {
          const editing = isEditing(field);
          
          return (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)' }}>{label}</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {confidence && <ConfidenceBadge confidence={confidence} />}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <input
                  type={type}
                  value={value}
                  onChange={(e) => {
                    if (editing) {
                      setEditableEnrichment(prev => prev ? { ...prev, [field]: e.target.value } : null);
                    }
                  }}
                  readOnly={!editing}
                  style={{
                    flex: 1,
                    padding: '0.75rem',
                    border: `1px solid ${editing ? 'var(--color-primary)' : 'var(--color-gray-200)'}`,
                    borderRadius: '8px',
                    fontSize: '0.9375rem',
                    background: editing ? 'var(--color-white)' : 'var(--color-gray-50)',
                    color: 'var(--color-gray-800)',
                    cursor: editing ? 'text' : 'default',
                    transition: 'all 0.15s ease',
                  }}
                />
                <button
                  onClick={() => toggleEditField(field)}
                  style={{
                    width: '36px',
                    height: '36px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: 'none',
                    borderRadius: '8px',
                    background: editing ? 'var(--color-success)' : 'var(--color-gray-100)',
                    color: editing ? 'white' : 'var(--color-gray-500)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    flexShrink: 0,
                  }}
                  title={editing ? 'Save changes' : 'Edit field'}
                  onMouseOver={(e) => {
                    if (!editing) {
                      e.currentTarget.style.background = 'var(--color-gray-200)';
                      e.currentTarget.style.color = 'var(--color-primary)';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!editing) {
                      e.currentTarget.style.background = 'var(--color-gray-100)';
                      e.currentTarget.style.color = 'var(--color-gray-500)';
                    }
                  }}
                >
                  {editing ? <CheckIcon /> : <PencilIcon />}
                </button>
              </div>
            </div>
          );
        };

        return (
          <div style={{ maxWidth: '900px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <Card padding="lg">
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Review Company Data
              </h2>
              <p style={{ margin: '0 0 1.5rem 0', fontSize: '0.8125rem', color: 'var(--color-gray-500)' }}>
                Click the pencil icon to edit any field if needed.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <ReviewField
                  field="companyName"
                  label="Company Name"
                  value={editableEnrichment?.companyName || ''}
                  confidence={editableEnrichment?.confidence?.companyName}
                />

                <ReviewField
                  field="legalEntityName"
                  label="Legal Entity Name"
                  value={editableEnrichment?.legalEntityName || ''}
                  confidence={editableEnrichment?.confidence?.legalEntityName}
                />

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <ReviewField
                    field="industry"
                    label="Industry"
                    value={editableEnrichment?.industry || ''}
                    confidence={editableEnrichment?.confidence?.industry}
                  />
                  <ReviewField
                    field="employeeBand"
                    label="Employee Band"
                    value={editableEnrichment?.employeeBand || ''}
                    confidence={editableEnrichment?.confidence?.employeeBand}
                  />
                </div>

                <ReviewField
                  field="hqLocation"
                  label="HQ Location"
                  value={editableEnrichment?.hqLocation || ''}
                  confidence={editableEnrichment?.confidence?.hqLocation}
                />

                <ReviewField
                  field="website"
                  label="Website"
                  value={editableEnrichment?.website || ''}
                  type="url"
                />
              </div>

              {error && (
                <div style={{
                  padding: '0.75rem 1rem',
                  background: 'rgba(220, 38, 38, 0.08)',
                  border: '1px solid rgba(220, 38, 38, 0.2)',
                  borderRadius: '8px',
                  color: 'var(--color-error)',
                  fontSize: '0.875rem',
                  marginTop: '1rem',
                }}>
                  {error}
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <Button variant="secondary" onClick={goBack}>
                  Back
                </Button>
                <Button onClick={handleFinalSubmit} isLoading={isLoading} style={{ flex: 1 }}>
                  {draft.decision === 'link' ? 'Link Company' : 'Create Company'}
                </Button>
              </div>
            </Card>

            <div>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-gray-500)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Payload Preview
              </h3>
              <JsonViewer
                title="HubSpot API Request"
                data={{
                  name: editableEnrichment?.companyName || '',
                  domain: draft.canonicalDomain,
                  legalEntityName: editableEnrichment?.legalEntityName || '',
                  ownerEmail: draft.ownerEmail,
                  industry: editableEnrichment?.industry || null,
                  employeeBand: editableEnrichment?.employeeBand || null,
                  hqLocation: editableEnrichment?.hqLocation || null,
                  website: editableEnrichment?.website || null,
                }}
              />
              <p style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--color-gray-400)' }}>
                This is the data that will be sent to HubSpot.
              </p>
            </div>
          </div>
        );

      case 'done':
        return (
          <Card padding="lg" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
            <div
              style={{
                width: '80px',
                height: '80px',
                margin: '0 auto 1.5rem',
                borderRadius: '50%',
                background: 'var(--color-success-light)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
              {draft.decision === 'link' ? 'Company Linked!' : 'Company Created!'}
            </h2>
            <p style={{ margin: '0 0 2rem 0', color: 'var(--color-gray-500)' }}>
              {draft.decision === 'link'
                ? 'The company has been linked to your records.'
                : 'A new company has been added to HubSpot.'}
            </p>

            {result && (
              <div style={{
                background: 'var(--color-gray-50)',
                borderRadius: '12px',
                padding: '1.5rem',
                marginBottom: '2rem',
                textAlign: 'left',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '10px',
                      background: 'var(--color-primary-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'var(--color-primary)',
                      fontWeight: 700,
                      fontSize: '1.25rem',
                    }}
                  >
                    {result.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                      {result.name}
                    </h3>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                      {result.domain}
                    </p>
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.875rem' }}>
                  <div>
                    <span style={{ color: 'var(--color-gray-500)' }}>ID:</span>{' '}
                    <code style={{ background: 'var(--color-gray-200)', padding: '0.125rem 0.375rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                      {result.id}
                    </code>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-gray-500)' }}>Owner:</span>{' '}
                    <span style={{ color: 'var(--color-gray-800)' }}>{result.ownerEmail || draft.ownerEmail}</span>
                  </div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
              <Button
                variant="outline"
                onClick={() => window.open('https://app.hubspot.com', '_blank')}
                leftIcon={
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                }
              >
                Open in HubSpot
              </Button>
              <Button
                onClick={() => {
                  navigate(`/hubspot/contact?companyId=${result?.id}&companyName=${encodeURIComponent(result?.name || '')}`);
                }}
              >
                Create Contact
              </Button>
            </div>

            <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-gray-200)' }}>
              <button
                onClick={resetWizard}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--color-gray-500)',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  textDecoration: 'underline',
                }}
              >
                Create another company
              </button>
            </div>
          </Card>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <Stepper
        steps={STEPS}
        currentStep={currentStep}
        completedSteps={completedSteps}
      />
      {renderStepContent()}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

