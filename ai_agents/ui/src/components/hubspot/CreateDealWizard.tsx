import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { DealDraft, HubSpotDeal } from '../../types/hubspot';
import {
  searchHubspotDeals,
  createHubspotDeal,
  linkExistingDeal,
  searchCompaniesForDropdown,
  getContactsByCompany,
  MOCK_PRODUCTS,
  MOCK_STAGES,
} from '../../services/mockHubspot';
import { Button, Input, Stepper, Card, Badge, JsonViewer, RadioGroup, SearchableSelect, Select, MultiSelect } from './ui';
import { useToast } from './ui/Toast';

type Step = 'input' | 'match' | 'review' | 'done';

const STEPS = [
  { id: 'input', title: 'Input' },
  { id: 'match', title: 'Match' },
  { id: 'review', title: 'Review' },
  { id: 'done', title: 'Done' },
];

const initialDraft: DealDraft = {
  product: '',
  companyId: '',
  contactIds: [],
  stage: 'Qualification',
};

export const CreateDealWizard = () => {
  const [searchParams] = useSearchParams();
  const { showToast } = useToast();
  const [currentStep, setCurrentStep] = useState<Step>('input');
  const [draft, setDraft] = useState<DealDraft>(initialDraft);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<HubSpotDeal | null>(null);
  const [companyOptions, setCompanyOptions] = useState<Array<{ value: string; label: string; secondary?: string }>>([]);
  const [contactOptions, setContactOptions] = useState<Array<{ value: string; label: string; secondary?: string }>>([]);

  // Prefill from URL params
  useEffect(() => {
    const companyId = searchParams.get('companyId');
    const contactId = searchParams.get('contactId');
    if (companyId) {
      setDraft(prev => ({
        ...prev,
        companyId,
        contactIds: contactId ? [contactId] : [],
      }));
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

  // Load contacts when company changes
  useEffect(() => {
    const loadContacts = async () => {
      if (draft.companyId) {
        const contacts = await getContactsByCompany(draft.companyId);
        setContactOptions(contacts.map(c => ({
          value: c.id,
          label: c.name,
          secondary: c.email,
        })));
      } else {
        setContactOptions([]);
      }
    };
    loadContacts();
  }, [draft.companyId]);

  const completedSteps = STEPS.slice(0, STEPS.findIndex(s => s.id === currentStep)).map(s => s.id);

  const updateDraft = useCallback((updates: Partial<DealDraft>) => {
    setDraft(prev => ({ ...prev, ...updates }));
  }, []);

  // Step 1: Input
  const handleInputSubmit = async () => {
    if (!draft.product || !draft.companyId || draft.contactIds.length === 0) {
      setError('Please fill in all required fields');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const matches = await searchHubspotDeals({
        companyId: draft.companyId,
        product: draft.product,
      });
      updateDraft({ matchResults: matches });

      // Default to link if match found
      if (matches.length > 0) {
        updateDraft({
          decision: 'link',
          selectedExistingDealId: matches[0].id,
        });
      } else {
        updateDraft({ decision: 'create' });
      }

      setCurrentStep('match');
    } catch (err) {
      setError('Failed to search for deals. Please try again.');
      showToast('Failed to search for deals', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Match
  const handleMatchContinue = () => {
    if (draft.decision === 'link' && !draft.selectedExistingDealId) {
      setError('Please select a deal to link');
      return;
    }
    setError(null);
    setCurrentStep('review');
  };

  // Step 3: Review & Create/Link
  const handleFinalSubmit = async () => {
    setIsLoading(true);
    setError(null);

    try {
      let deal: HubSpotDeal;

      if (draft.decision === 'link' && draft.selectedExistingDealId) {
        deal = await linkExistingDeal(draft.selectedExistingDealId, {
          contactIds: draft.contactIds,
        });
        showToast('Deal linked successfully!', 'success');
      } else {
        deal = await createHubspotDeal({
          product: draft.product,
          companyId: draft.companyId,
          contactIds: draft.contactIds,
          ownerEmail: draft.ownerEmail,
          stage: draft.stage,
          amount: draft.amount,
        });
        showToast('Deal created successfully!', 'success');
      }

      setResult(deal);
      setCurrentStep('done');
    } catch (err) {
      setError('Failed to complete operation. Please try again.');
      showToast('Operation failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const goBack = () => {
    const stepOrder: Step[] = ['input', 'match', 'review', 'done'];
    const currentIndex = stepOrder.indexOf(currentStep);
    if (currentIndex > 0) {
      setCurrentStep(stepOrder[currentIndex - 1]);
    }
  };

  const resetWizard = () => {
    setDraft(initialDraft);
    setCurrentStep('input');
    setResult(null);
    setError(null);
  };

  const productOptions = MOCK_PRODUCTS.map(p => ({
    value: p.name,
    label: p.name,
  }));

  const stageOptions = MOCK_STAGES.map(s => ({
    value: s.name,
    label: s.name,
  }));

  const selectedCompany = companyOptions.find(c => c.value === draft.companyId);

  // Render Step Content
  const renderStepContent = () => {
    switch (currentStep) {
      case 'input':
        return (
          <Card padding="lg" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Create Deal
              </h2>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                We'll check for existing deals first to prevent duplicates.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <Select
                label="Product"
                options={productOptions}
                value={draft.product}
                onChange={(value) => updateDraft({ product: value })}
                placeholder="Select a product..."
                required
              />

              <SearchableSelect
                label="Company"
                options={companyOptions}
                value={draft.companyId}
                onChange={(value) => updateDraft({ companyId: value, contactIds: [] })}
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

              <MultiSelect
                label="Contacts"
                options={contactOptions}
                values={draft.contactIds}
                onChange={(values) => updateDraft({ contactIds: values })}
                placeholder={draft.companyId ? 'Select contacts...' : 'Select a company first'}
                required
                isLoading={!!draft.companyId && contactOptions.length === 0}
              />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <Select
                  label="Stage"
                  options={stageOptions}
                  value={draft.stage || 'Qualification'}
                  onChange={(value) => updateDraft({ stage: value })}
                />
                <Input
                  label="Amount"
                  type="number"
                  placeholder="50000"
                  value={draft.amount?.toString() || ''}
                  onChange={(e) => updateDraft({ amount: e.target.value ? Number(e.target.value) : undefined })}
                  hint="Deal value in USD"
                />
              </div>

              <Input
                label="Owner Email (Optional)"
                type="email"
                placeholder="owner@yourcompany.com"
                value={draft.ownerEmail || ''}
                onChange={(e) => updateDraft({ ownerEmail: e.target.value })}
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
                disabled={!draft.product || !draft.companyId || draft.contactIds.length === 0}
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
                Existing Deals Check
              </h2>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                Checking for deals with <strong>{draft.product}</strong> for <strong>{selectedCompany?.label}</strong>
              </p>
            </div>

            {draft.matchResults && draft.matchResults.length > 0 ? (
              <>
                <div style={{
                  padding: '0.75rem 1rem',
                  background: 'rgba(245, 158, 11, 0.08)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  borderRadius: '8px',
                  marginBottom: '1.5rem',
                  fontSize: '0.875rem',
                  color: '#b45309',
                }}>
                  ⚠️ We found {draft.matchResults.length} existing deal{draft.matchResults.length > 1 ? 's' : ''} for this company and product. Consider linking instead of creating a duplicate.
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-gray-700)' }}>
                    Existing Deals
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {draft.matchResults.map((deal) => (
                      <label
                        key={deal.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          padding: '1rem',
                          border: `2px solid ${draft.selectedExistingDealId === deal.id ? 'var(--color-primary)' : 'var(--color-gray-200)'}`,
                          borderRadius: '8px',
                          cursor: 'pointer',
                          background: draft.selectedExistingDealId === deal.id ? 'rgba(46, 49, 190, 0.04)' : 'var(--color-white)',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        <input
                          type="radio"
                          name="existingDeal"
                          checked={draft.selectedExistingDealId === deal.id}
                          onChange={() => updateDraft({ selectedExistingDealId: deal.id, decision: 'link' })}
                          style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary)' }}
                        />
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, color: 'var(--color-gray-900)' }}>{deal.name}</div>
                          <div style={{ fontSize: '0.8125rem', color: 'var(--color-gray-500)', display: 'flex', gap: '0.75rem', marginTop: '0.25rem' }}>
                            <span>Stage: {deal.stage}</span>
                            {deal.amount && <span>Amount: ${deal.amount.toLocaleString()}</span>}
                          </div>
                        </div>
                        <Badge variant="warning">{deal.stage}</Badge>
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
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>✨</div>
                <p style={{ margin: 0, color: 'var(--color-gray-600)', fontWeight: 500 }}>
                  No existing deals found
                </p>
                <p style={{ margin: '0.25rem 0 0', color: 'var(--color-gray-500)', fontSize: '0.875rem' }}>
                  You're clear to create a new deal for this company and product.
                </p>
              </div>
            )}

            <RadioGroup
              name="decision"
              label="What would you like to do?"
              options={[
                {
                  value: 'link',
                  label: 'Link to Existing Deal',
                  description: draft.matchResults?.length ? 'Add contacts to an existing deal' : 'No matching deals found',
                },
                {
                  value: 'create',
                  label: 'Create New Deal',
                  description: 'Start a fresh deal for this opportunity',
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
              <Button onClick={handleMatchContinue} style={{ flex: 2 }}>
                Continue to Review
              </Button>
            </div>
          </Card>
        );

      case 'review':
        return (
          <div style={{ maxWidth: '900px', margin: '0 auto', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <Card padding="lg">
              <h2 style={{ margin: '0 0 1.5rem 0', fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                Review Deal Details
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{
                  padding: '1rem',
                  background: 'var(--color-gray-50)',
                  borderRadius: '8px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Badge variant={draft.decision === 'link' ? 'info' : 'success'}>
                      {draft.decision === 'link' ? 'Linking' : 'Creating'}
                    </Badge>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-600)' }}>
                    {draft.decision === 'link'
                      ? 'Contacts will be added to the selected existing deal.'
                      : 'A new deal will be created with the following details.'}
                  </p>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                    Product
                  </label>
                  <div style={{
                    padding: '0.75rem',
                    background: 'var(--color-gray-50)',
                    border: '1px solid var(--color-gray-200)',
                    borderRadius: '8px',
                    color: 'var(--color-gray-800)',
                  }}>
                    {draft.product}
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                    Company
                  </label>
                  <div style={{
                    padding: '0.75rem',
                    background: 'var(--color-gray-50)',
                    border: '1px solid var(--color-gray-200)',
                    borderRadius: '8px',
                    color: 'var(--color-gray-800)',
                  }}>
                    {selectedCompany?.label}
                    {selectedCompany?.secondary && (
                      <span style={{ color: 'var(--color-gray-500)', marginLeft: '0.5rem' }}>
                        ({selectedCompany.secondary})
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                    Contacts ({draft.contactIds.length})
                  </label>
                  <div style={{
                    padding: '0.75rem',
                    background: 'var(--color-gray-50)',
                    border: '1px solid var(--color-gray-200)',
                    borderRadius: '8px',
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '0.5rem',
                  }}>
                    {draft.contactIds.map(id => {
                      const contact = contactOptions.find(c => c.value === id);
                      return (
                        <span
                          key={id}
                          style={{
                            padding: '0.25rem 0.5rem',
                            background: 'var(--color-primary-light)',
                            color: 'var(--color-primary)',
                            borderRadius: '4px',
                            fontSize: '0.8125rem',
                            fontWeight: 500,
                          }}
                        >
                          {contact?.label || id}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {draft.decision === 'create' && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                        Stage
                      </label>
                      <Select
                        options={stageOptions}
                        value={draft.stage || 'Qualification'}
                        onChange={(value) => updateDraft({ stage: value })}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontWeight: 600, fontSize: '0.875rem', color: 'var(--color-gray-700)', marginBottom: '0.5rem' }}>
                        Amount
                      </label>
                      <Input
                        type="number"
                        placeholder="50000"
                        value={draft.amount?.toString() || ''}
                        onChange={(e) => updateDraft({ amount: e.target.value ? Number(e.target.value) : undefined })}
                      />
                    </div>
                  </div>
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
                  {draft.decision === 'link' ? 'Link Deal' : 'Create Deal'}
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
                  product: draft.product,
                  companyId: draft.companyId,
                  contactIds: draft.contactIds,
                  stage: draft.stage || 'Qualification',
                  amount: draft.amount || null,
                  ownerEmail: draft.ownerEmail || null,
                  action: draft.decision,
                  ...(draft.decision === 'link' ? { existingDealId: draft.selectedExistingDealId } : {}),
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
              {draft.decision === 'link' ? 'Deal Linked!' : 'Deal Created!'}
            </h2>
            <p style={{ margin: '0 0 2rem 0', color: 'var(--color-gray-500)' }}>
              {draft.decision === 'link'
                ? 'Contacts have been added to the existing deal.'
                : 'A new deal has been created in HubSpot.'}
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
                      background: 'linear-gradient(135deg, var(--color-success) 0%, #059669 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="4" width="20" height="16" rx="2" />
                      <path d="M12 9v6" />
                      <path d="M9 12h6" />
                    </svg>
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-gray-900)' }}>
                      {result.name}
                    </h3>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-gray-500)' }}>
                      {result.product}
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
                    <span style={{ color: 'var(--color-gray-500)' }}>Stage:</span>{' '}
                    <Badge variant="info">{result.stage}</Badge>
                  </div>
                  {result.amount && (
                    <div style={{ gridColumn: '1 / -1' }}>
                      <span style={{ color: 'var(--color-gray-500)' }}>Amount:</span>{' '}
                      <span style={{ fontWeight: 600, color: 'var(--color-success)' }}>
                        ${result.amount.toLocaleString()}
                      </span>
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
                Create another deal
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
    </div>
  );
};


