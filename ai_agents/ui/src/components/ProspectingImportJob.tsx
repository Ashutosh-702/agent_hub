import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, NotificationBanner, SelectorDropdown, Spinner, Typography } from 'novus';
import { useNavigate } from 'react-router-dom';
import { ProspectingWizardLayout } from './ProspectingWizardLayout';

type StepKey = 'searching' | 'dedupe' | 'grouping';
type StepState = 'done' | 'active' | 'pending';

const stepOrder: StepKey[] = ['searching', 'dedupe', 'grouping'];

const stepLabel: Record<StepKey, string> = {
  searching: 'Searching Apollo...',
  dedupe: 'Removing duplicates...',
  grouping: 'Grouping by company...',
};

export const ProspectingImportJob = () => {
  const navigate = useNavigate();
  const [tick, setTick] = useState(0);
  const [importLimit, setImportLimit] = useState<{ label: string; value: string }>({
    label: '200 contacts',
    value: '200',
  });
  const [onlyVerified, setOnlyVerified] = useState(true);

  // Mock progress: advance every 1.2s and then stop
  useEffect(() => {
    const id = window.setInterval(() => setTick(t => t + 1), 1200);
    return () => window.clearInterval(id);
  }, []);

  const phase = Math.min(tick, stepOrder.length);
  const isComplete = phase >= stepOrder.length;

  const steps = useMemo(() => {
    const states: Record<StepKey, StepState> = {
      searching: 'pending',
      dedupe: 'pending',
      grouping: 'pending',
    };
    stepOrder.forEach((k, idx) => {
      if (idx < phase - 1) states[k] = 'done';
      else if (idx === phase - 1) states[k] = 'active';
    });
    if (isComplete) {
      stepOrder.forEach(k => (states[k] = 'done'));
    }
    return states;
  }, [phase, isComplete]);

  const progressPct = isComplete ? 100 : Math.max(5, Math.round((phase / stepOrder.length) * 100));

  return (
    <ProspectingWizardLayout
      title="Prospecting — Import Job"
      primaryCtaText={isComplete ? 'Import and Review' : 'Import and Review'}
      activeStep="import-job"
      onPrimaryCta={() => navigate('/prospecting/wide/review-prospects')}
    >
      <div className="figma-wizard-inline-banner">
        <NotificationBanner
          appearance={isComplete ? 'positive' : 'neutral'}
          type="inline"
          title={isComplete ? undefined : undefined}
          description={
            isComplete
              ? 'Successfully fetched prospects from Apollo!'
              : 'Fetching from Apollo... This may take a minute.'
          }
          showIcon
        />
      </div>

      {!isComplete ? (
        <div className="figma-card figma-import-card">
          <div className="figma-import-center">
            <Spinner size="l" label="Removing duplicates..." labelPlacement="bottom" />
            <div className="figma-progressbar">
              <div className="figma-progressbar-fill" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="figma-import-steps">
              {stepOrder.map(k => (
                <div key={k} className="figma-import-step">
                  <span className={`figma-step-icon ${steps[k]}`}>
                    {steps[k] === 'done' ? '✓' : steps[k] === 'active' ? '◌' : ''}
                  </span>
                  <span className={`figma-import-step-text ${steps[k]}`}>{stepLabel[k]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="figma-card">
          <div className="figma-stats-grid">
            <div className="figma-stat">
              <div className="figma-stat-title">Contacts Found</div>
              <div className="figma-stat-value">
                <span>384</span>
                <Badge state="neutral" emphasis="subtle">
                  From Apollo
                </Badge>
              </div>
            </div>
            <div className="figma-stat">
              <div className="figma-stat-title">Companies Found</div>
              <div className="figma-stat-value">
                <span>52</span>
                <Badge state="neutral" emphasis="subtle">
                  Grouped
                </Badge>
              </div>
            </div>
          </div>

          <div className="figma-form-grid" style={{ marginTop: 16 }}>
            <div className="figma-form-row">
              <div className="figma-label">Import Limit</div>
              <div>
                <SelectorDropdown
                  label=""
                  size="m"
                  options={[
                    { label: '50 contacts', value: '50' },
                    { label: '100 contacts', value: '100' },
                    { label: '200 contacts', value: '200' },
                    { label: '500 contacts', value: '500' },
                  ]}
                  value={importLimit}
                  onChange={(opt: any) => setImportLimit(opt)}
                />
                <div style={{ marginTop: 6 }}>
                  <Typography variant="body-s" type="p" className="figma-muted">
                    We&apos;ll import up to {importLimit.value} contacts
                  </Typography>
                </div>
              </div>
            </div>

            <div className="figma-form-row figma-switch-row">
              <div>
                <div className="figma-label">Only Verified Emails</div>
                <Typography variant="body-s" type="p" className="figma-muted">
                  Filter out unverified email addresses
                </Typography>
              </div>
              <button
                type="button"
                className={`figma-switch ${onlyVerified ? 'on' : ''}`}
                onClick={() => setOnlyVerified(v => !v)}
                aria-label="Toggle only verified emails"
              >
                <span className="figma-switch-knob" />
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="figma-wizard-bottom-cta">
        <Button
          type="primary"
          appearance="default"
          size="m"
          className="figma-primary-cta"
          onClick={() => navigate('/prospecting/wide/review-prospects')}
          disabled={!isComplete}
        >
          Import and Review
        </Button>
      </div>
    </ProspectingWizardLayout>
  );
};


