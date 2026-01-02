import { useState, useCallback, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type { ContactDraft, ContactEnrichment, HubSpotContact } from '../../types/hubspot';
import {
  searchHubspotContacts,
  enrichContact,
  createHubspotContact,
  linkExistingContact,
  searchCompaniesForDropdown,
} from '../../services/mockHubspot';
import { Button, Input, Stepper, Card, Badge, JsonViewer, RadioGroup, SearchableSelect, Select } from './ui';
import { useToast } from './ui/Toast';
import { ConfidenceBadge } from './ui/Badge';

type Step = 'input' | 'match' | 'enrich' | 'review' | 'done';

const STEPS = [
  { id: 'input', title: 'Input' },
  { id: 'match', title: 'Match' },
  { id: 'enrich', title: 'Enrich' },
  { id: 'review', title: 'Review' },
  { id: 'done', title: 'Done' },
];

const initialDraft: ContactDraft = {
  firstName: '',
  lastName: '',
  email: '',
  associateType: 'company',
  associateId: '',
};

export const CreateContactWizard = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState<Step>('input');
  const [draft, setDraft] = useState<ContactDraft>(initialDraft);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HubSpotContact | null>(null);
  const [editableEnrichment, setEditableEnrichment] = useState<ContactEnrichment | null>(null);
  const [runEnrichment, setRunEnrichment] = useState(true);
  const [companyOptions, setCompanyOptions] = useState<Array<{ value: string; label: string; secondary?: string }>>([]);

  // Prefill from URL params
  useEffect(() => {
    const companyId = searchParams.get('companyId');
    const companyName = searchParams.get('companyName');
    if (companyId) {
      setDraft(prev => ({
        ...prev,
        associateType: 'company',
        associateId: companyId,
      }));
      if (companyName) {
        setCompanyOptions([{ value: companyId, label: companyName }]);
      }
    }
  }, [searchParams]);

  // Load company options
  useEffect(() => {
    const loadCompanies = async () => {
      const companies = await searchCompaniesForDropdown('');
      setCompanyOptions(companies.map(c => ({
        value: c.id,
        label: c.name,
        secondary: c.domain,
      })));
    };
    loadCompanies();
  }, []);

  const completedSteps = STEPS.slice(0, STEPS.findIndex(s => s.id === currentStep)).map(s => s.id);

  const updateDraft = useCallback((updates: Partial<ContactDraft>) => {
    setDraft(prev => ({ ...prev, ...updates }));
  }, []);

  // Step 1: Input
  const handleInputSubmit = async () => {
    if (!draft.email || !draft.associateId) {
      setError('Please fill in all required fields');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const matches = await searchHubspotContacts({ email: draft.email });
      updateDraft({ matchResults: matches });

      // Default to link if exact match found
      if (matches.length > 0) {
        const exactMatch = matches.find(m => m.email.toLowerCase() === draft.email.toLowerCase());
        if (exactMatch) {
          updateDraft({
            decision: 'link',
            selectedExistingContactId: exactMatch.id,
          });
        }
      } else {
        updateDraft({ decision: 'create' });
      }

      setCurrentStep('match');
    } catch (err) {
      setError('Failed to search for contacts. Please try again.');
      showToast('Failed to search for contacts', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Match
  const handleMatchContinue = () => {
    if (draft.decision === 'link' && !draft.selectedExistingContactId) {
      setError('Please select a contact to link');
      return;
    }
    setError(null);
    setCurrentStep('enrich');
    if (runEnrichment) {
      handleEnrich();
    } else {
      // Skip enrichment
      setEditableEnrichment({
        confidence: {},
      });
      setCurrentStep('review');
    }
  };

  // Step 3: Enrich
  const handleEnrich = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const enriched = await enrichContact({ email: draft.email });
      updateDraft({ enriched });
      setEditableEnrichment({ ...enriched });
      setCurrentStep('review');
    } catch (err) {
      setError('Failed to enrich contact data. Please try again.');
      showToast('Enrichment failed', 'error');
      setEditableEnrichment({ confidence: {} });
      setCurrentStep('review');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 4: Review & Create/Link
  const handleFinalSubmit = async () => {
    setIsLoading(true);
    setError(null);

    try {
      let contact: HubSpotContact;

      if (draft.decision === 'link' && draft.selectedExistingContactId) {
        contact = await linkExistingContact(draft.selectedExistingContactId, {
          enrichedData: editableEnrichment,
          associateType: draft.associateType,
          associateId: draft.associateId,
        });
        showToast('Contact linked successfully!', 'success');
      } else {
        contact = await createHubspotContact({
          firstName: draft.firstName,
          lastName: draft.lastName,
          email: draft.email,
          phone: editableEnrichment?.phone,
          linkedIn: editableEnrichment?.linkedIn,
          title: editableEnrichment?.title,
          department: editableEnrichment?.department,
          associateType: draft.associateType,
          associateId: draft.associateId,
        });
        showToast('Contact created successfully!', 'success');
      }

      setResult(contact);
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
      if (currentStep === 'review' && !runEnrichment) {
        setCurrentStep('match');
      } else {
        setCurrentStep(stepOrder[currentIndex - 1]);
      }
    }
  };

  const resetWizard = () => {
    setDraft(initialDraft);
    setCurrentStep('input');
    setResult(null);
    setEditableEnrichment(null);
    setError(null);
    setRunEnrichment(true);
  };

  // Render Step Content
  const renderStepContent = () => {
    switch (currentStep) {
      case 'input':
        return (
          <Card padding="lg" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Enter Contact Details
              </h2>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                We'll search HubSpot for existing matches first.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <Input
                  label="First Name"
                  placeholder="John"
                  value={draft.firstName}
                  onChange={(e) => updateDraft({ firstName: e.target.value })}
                />
                <Input
                  label="Last Name"
                  placeholder="Smith"
                  value={draft.lastName}
                  onChange={(e) => updateDraft({ lastName: e.target.value })}
                />
              </div>

              <Input
                label="Email"
                type="email"
                placeholder="john.smith@company.com"
                value={draft.email}
                onChange={(e) => updateDraft({ email: e.target.value })}
                required
              />

              <Select
                label="Associate With"
                options={[
                  { value: 'company', label: 'Company' },
                  { value: 'deal', label: 'Deal' },
                ]}
                value={draft.associateType}
                onChange={(value) => updateDraft({ associateType: value as 'company' | 'deal', associateId: '' })}
                required
              />

              {draft.associateType === 'company' ? (
                <SearchableSelect
                  label="Company"
                  options={companyOptions}
                  value={draft.associateId}
                  onChange={(value) => updateDraft({ associateId: value })}
                  placeholder="Search for a company..."
                  required
                  onSearch={async (query) => {
                    const companies = await searchCompaniesForDropdown(query);
                    setCompanyOptions(companies.map(c => ({
                      value: c.id,
                      label: c.name,
                      secondary: c.domain,
                    })));
                  }}
                />
              ) : (
                <Input
                  label="Deal ID"
                  placeholder="deal_123"
                  value={draft.associateId}
                  onChange={(e) => updateDraft({ associateId: e.target.value })}
                  required
                  hint="Enter the HubSpot Deal ID"
                />
              )}

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
                disabled={!draft.email || !draft.associateId}
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
                Email: <code style={{ background: 'var(--color-gray-100)', padding: '0.125rem 0.5rem', borderRadius: '4px' }}>{draft.email}</code>
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
                    Existing Contacts
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {draft.matchResults.map((contact) => (
                      <label
                        key={contact.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          padding: '1rem',
                          border: `2px solid ${draft.selectedExistingContactId === contact.id ? 'var(--color-primary)' : 'var(--color-gray-200)'}`,
                          borderRadius: '8px',
                          cursor: 'pointer',
                          background: draft.selectedExistingContactId === contact.id ? 'rgba(46, 49, 190, 0.04)' : 'var(--color-white)',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="radio"
                          name="existingContact"
                          checked={draft.selectedExistingContactId === contact.id}
                          onChange={() => updateDraft({ selectedExistingContactId: contact.id, decision: 'link' })}
                          style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary)' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: 'var(--color-gray-900)' }}>{contact.name}</div>
                          <div style={{ fontSize: '0.8125rem', color: 'var(--color-gray-500)' }}>
                            {contact.email} {contact.phone && `• ${contact.phone}`}
                          </div>
                        </div>
                        {contact.email.toLowerCase() === draft.email.toLowerCase() && (
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
                  No existing contacts found for this email. A new contact will be created.
                </p>
              </div>
            )}

            <RadioGroup
              name="decision"
              label="What would you like to do?"
              options={[
                {
                  value: 'link',
                  label: 'Link to Existing Contact',
                  description: draft.matchResults?.length ? 'Connect to a contact that already exists in HubSpot' : 'No matching contacts found',
                },
                {
                  value: 'create',
                  label: 'Create New Contact',
                  description: 'Add a brand new contact record to HubSpot',
                },
              ]}
              value={draft.decision}
              onChange={(value) => updateDraft({ decision: value as 'link' | 'create' })}
            />

            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: 'var(--color-gray-50)',
              borderRadius: '8px',
            }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={runEnrichment}
                  onChange={(e) => setRunEnrichment(e.target.checked)}
                  style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary)' }}
                />
                <div>
                  <span style={{ fontWeight: 600, color: 'var(--color-gray-800)' }}>
                    Run enrichment to fetch phone/LinkedIn
                  </span>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--color-gray-500)' }}>
                    Get additional contact details automatically
                  </p>
                </div>
              </label>
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
              <Button variant="secondary" onClick={goBack} style={{ flex: 1 }}>
                Back
              </Button>
              <Button onClick={handleMatchContinue} isLoading={isLoading} style={{ flex: 2 }}>
                {runEnrichment ? 'Continue to Enrich' : 'Continue to Review'}
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
              Enriching Contact Data...
            </h2>
            <p style={{ margin: 0, color: 'var(--color-gray-500)', fontSize: '0.875rem' }}>
              We're fetching additional contact information like phone and LinkedIn.
            </p>
          </Card>
        );

      case 'review':
        return (
          <div style={{ maxWidth: '900px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <Card padding="lg">
              <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Review & Edit Contact Data
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                      First Name
                    </label>
                    <input
                      type="text"
                      value={draft.firstName}
                      onChange={(e) => updateDraft({ firstName: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid var(--color-gray-300)',
                        borderRadius: '8px',
                        fontSize: '0.9375rem',
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                      Last Name
                    </label>
                    <input
                      type="text"
                      value={draft.lastName}
                      onChange={(e) => updateDraft({ lastName: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '0.75rem',
                        border: '1px solid var(--color-gray-300)',
                        borderRadius: '8px',
                        fontSize: '0.9375rem',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                    Email
                  </label>
                  <input
                    type="email"
                    value={draft.email}
                    disabled
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: '1px solid var(--color-gray-200)',
                      borderRadius: '8px',
                      fontSize: '0.9375rem',
                      background: 'var(--color-gray-50)',
                      color: 'var(--color-gray-500)',
                    }}
                  />
                </div>

                {editableEnrichment && (
                  <>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)' }}>Phone</label>
                        {editableEnrichment.confidence?.phone && (
                          <ConfidenceBadge confidence={editableEnrichment.confidence.phone} />
                        )}
                      </div>
                      <input
                        type="tel"
                        value={editableEnrichment.phone || ''}
                        onChange={(e) => setEditableEnrichment(prev => prev ? { ...prev, phone: e.target.value } : null)}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          border: '1px solid var(--color-gray-300)',
                          borderRadius: '8px',
                          fontSize: '0.9375rem',
                        }}
                      />
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)' }}>LinkedIn</label>
                        {editableEnrichment.confidence?.linkedIn && (
                          <ConfidenceBadge confidence={editableEnrichment.confidence.linkedIn} />
                        )}
                      </div>
                      <input
                        type="url"
                        value={editableEnrichment.linkedIn || ''}
                        onChange={(e) => setEditableEnrichment(prev => prev ? { ...prev, linkedIn: e.target.value } : null)}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          border: '1px solid var(--color-gray-300)',
                          borderRadius: '8px',
                          fontSize: '0.9375rem',
                        }}
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                          <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)' }}>Title</label>
                          {editableEnrichment.confidence?.title && (
                            <ConfidenceBadge confidence={editableEnrichment.confidence.title} />
                          )}
                        </div>
                        <input
                          type="text"
                          value={editableEnrichment.title || ''}
                          onChange={(e) => setEditableEnrichment(prev => prev ? { ...prev, title: e.target.value } : null)}
                          style={{
                            width: '100%',
                            padding: '0.75rem',
                            border: '1px solid var(--color-gray-300)',
                            borderRadius: '8px',
                            fontSize: '0.9375rem',
                          }}
                        />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                          <label style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)' }}>Department</label>
                          {editableEnrichment.confidence?.department && (
                            <ConfidenceBadge confidence={editableEnrichment.confidence.department} />
                          )}
                        </div>
                        <input
                          type="text"
                          value={editableEnrichment.department || ''}
                          onChange={(e) => setEditableEnrichment(prev => prev ? { ...prev, department: e.target.value } : null)}
                          style={{
                            width: '100%',
                            padding: '0.75rem',
                            border: '1px solid var(--color-gray-300)',
                            borderRadius: '8px',
                            fontSize: '0.9375rem',
                          }}
                        />
                      </div>
                    </div>
                  </>
                )}
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
                  {draft.decision === 'link' ? 'Link Contact' : 'Create Contact'}
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
                  firstName: draft.firstName,
                  lastName: draft.lastName,
                  email: draft.email,
                  phone: editableEnrichment?.phone || null,
                  linkedIn: editableEnrichment?.linkedIn || null,
                  title: editableEnrichment?.title || null,
                  department: editableEnrichment?.department || null,
                  associateType: draft.associateType,
                  associateId: draft.associateId,
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
              {draft.decision === 'link' ? 'Contact Linked!' : 'Contact Created!'}
            </h2>
            <p style={{ margin: '0 0 2rem 0', color: 'var(--color-gray-500)' }}>
              {draft.decision === 'link'
                ? 'The contact has been linked to your records.'
                : 'A new contact has been added to HubSpot.'}
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
                      borderRadius: '50%',
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
                      {result.email}
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
                  {result.phone && (
                    <div>
                      <span style={{ color: 'var(--color-gray-500)' }}>Phone:</span>{' '}
                      <span style={{ color: 'var(--color-gray-800)' }}>{result.phone}</span>
                    </div>
                  )}
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
                  navigate(`/hubspot/deal?companyId=${draft.associateId}&contactId=${result?.id}`);
                }}
              >
                Create Deal
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
                Create another contact
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

