import { useMemo, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { Button, NotificationBanner, Typography } from 'novus';
import { useNavigate } from 'react-router-dom';
import { ProspectingWizardLayout } from './ProspectingWizardLayout';

type Chip = { id: string; label: string };

const DEFAULT_INDUSTRIES: Chip[] = [
  { id: 'saas', label: 'SaaS' },
  { id: 'cloud', label: 'Cloud Infrastructure' },
];
const DEFAULT_REGIONS: Chip[] = [
  { id: 'us', label: 'US' },
  { id: 'uk', label: 'UK' },
];
const DEFAULT_TITLES: Chip[] = [
  { id: 'vp-eng', label: 'VP Engineering' },
  { id: 'cto', label: 'CTO' },
  { id: 'dir-eng', label: 'Director of Engineering' },
];

export const ProspectingDefineFilters = () => {
  const navigate = useNavigate();
  const [industries, setIndustries] = useState<Chip[]>(DEFAULT_INDUSTRIES);
  const [regions, setRegions] = useState<Chip[]>(DEFAULT_REGIONS);
  const [titles, setTitles] = useState<Chip[]>(DEFAULT_TITLES);
  const [companySize, setCompanySize] = useState<'50-200' | '200-500' | '500-1000' | '1000+' | ''>('50-200');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const canProceed = useMemo(() => {
    return industries.length > 0 && regions.length > 0 && titles.length > 0 && companySize !== '';
  }, [industries.length, regions.length, titles.length, companySize]);

  const removeChip = (list: Chip[], id: string) => list.filter(c => c.id !== id);

  const addChip = (setter: Dispatch<SetStateAction<Chip[]>>, prefix: string) => {
    const label = window.prompt('Enter value');
    if (!label) return;
    setter((prev) => [...prev, { id: `${prefix}-${Date.now()}`, label }]);
  };

  return (
    <ProspectingWizardLayout
      title="Prospecting — Define Filters"
      primaryCtaText="Find Prospects"
      activeStep="define-filters"
      onPrimaryCta={() => navigate('/prospecting/wide/import-job')}
    >
      {!canProceed && (
        <div className="figma-wizard-inline-banner">
          <NotificationBanner
            appearance="warning"
            type="inline"
            title="Next:"
            description="Add at least one Industry, Region, Company Size, and Title."
            showIcon
          />
        </div>
      )}

      <div className="figma-card">
        <div className="figma-card-header">
          <Typography variant="heading-m" type="h2">
            Must-have filters
          </Typography>
        </div>

        <div className="figma-form-grid">
          <div className="figma-form-row">
            <div className="figma-label">
              Industry <span className="figma-required">*</span>
            </div>
            <div className="figma-chip-row">
              {industries.map(c => (
                <span key={c.id} className="figma-chip">
                  {c.label}
                  <button
                    type="button"
                    className="figma-chip-x"
                    onClick={() => setIndustries(prev => removeChip(prev, c.id))}
                    aria-label={`Remove ${c.label}`}
                  >
                    ×
                  </button>
                </span>
              ))}
              <Button
                type="secondary"
                appearance="default"
                size="s"
                className="figma-chip-add"
                onClick={() => addChip(setIndustries, 'industry')}
              >
                + Add Industry
              </Button>
            </div>
          </div>

          <div className="figma-form-row">
            <div className="figma-label">
              Region <span className="figma-required">*</span>
            </div>
            <div className="figma-chip-row">
              {regions.map(c => (
                <span key={c.id} className="figma-chip">
                  {c.label}
                  <button
                    type="button"
                    className="figma-chip-x"
                    onClick={() => setRegions(prev => removeChip(prev, c.id))}
                    aria-label={`Remove ${c.label}`}
                  >
                    ×
                  </button>
                </span>
              ))}
              <Button
                type="secondary"
                appearance="default"
                size="s"
                className="figma-chip-add"
                onClick={() => addChip(setRegions, 'region')}
              >
                + Add Region
              </Button>
            </div>
          </div>

          <div className="figma-form-row">
            <div className="figma-label">
              Company Size <span className="figma-required">*</span>
            </div>
            <div className="figma-pill-row">
              {(['50-200', '200-500', '500-1000', '1000+'] as const).map(v => (
                <button
                  key={v}
                  type="button"
                  className={`figma-pill ${companySize === v ? 'active' : ''}`}
                  onClick={() => setCompanySize(v)}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>

          <div className="figma-form-row">
            <div className="figma-label">
              Titles / Persona <span className="figma-required">*</span>
            </div>
            <div className="figma-chip-row">
              {titles.map(c => (
                <span key={c.id} className="figma-chip">
                  {c.label}
                  <button
                    type="button"
                    className="figma-chip-x"
                    onClick={() => setTitles(prev => removeChip(prev, c.id))}
                    aria-label={`Remove ${c.label}`}
                  >
                    ×
                  </button>
                </span>
              ))}
              <Button
                type="secondary"
                appearance="default"
                size="s"
                className="figma-chip-add"
                onClick={() => addChip(setTitles, 'title')}
              >
                + Add Title
              </Button>
            </div>
          </div>
        </div>

        <div className="figma-accordion">
          <button
            type="button"
            className="figma-accordion-btn"
            onClick={() => setShowAdvanced(v => !v)}
          >
            <span>Advanced Filters</span>
            <span className={`figma-accordion-caret ${showAdvanced ? 'open' : ''}`}>▾</span>
          </button>
          {showAdvanced && (
            <div className="figma-accordion-content">
              <Typography variant="body-s" type="p" className="figma-muted">
                Coming soon — we’ll add more filters here once APIs are available.
              </Typography>
              <div style={{ marginTop: 12 }}>
                <Button
                  type="tertiary"
                  appearance="default"
                  size="s"
                  onClick={() => navigate('/prospecting/wide/create')}
                >
                  Open legacy campaign creation form
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="figma-wizard-bottom-cta">
        <Button
          type="primary"
          appearance="default"
          size="m"
          className="figma-primary-cta"
          onClick={() => navigate('/prospecting/wide/import-job')}
          disabled={!canProceed}
        >
          Find Prospects
        </Button>
      </div>
    </ProspectingWizardLayout>
  );
};


