import { useMemo } from 'react';
import { Button } from 'novus';
import { useNavigate } from 'react-router-dom';
import { ProspectingWizardLayout } from './ProspectingWizardLayout';
import { ProspectsReviewTable, type ProspectCompany } from './ProspectsReviewTable';

const mockCompanies: ProspectCompany[] = [
  {
    id: 'techcorp',
    name: 'TechCorp Inc',
    domain: 'techcorp.com',
    region: 'US',
    size: '500-1000',
    contacts: [
      { id: 'c1', name: 'Sarah Chen', title: 'VP of Engineering', confidence: 'high' },
      { id: 'c2', name: 'Michael Roberts', title: 'Director of Product', confidence: 'high' },
      { id: 'c3', name: 'Emily Watson', title: 'Engineering Manager', confidence: 'medium' },
    ],
  },
  {
    id: 'dataflow',
    name: 'DataFlow Systems',
    domain: 'dataflow.io',
    region: 'UK',
    size: '200-500',
    contacts: [
      { id: 'd1', name: 'Ava Patel', title: 'VP Engineering', confidence: 'high' },
      { id: 'd2', name: 'Liam Scott', title: 'Engineering Director', confidence: 'medium' },
      { id: 'd3', name: 'Noah Reed', title: 'Platform Lead', confidence: 'low' },
      { id: 'd4', name: 'Mia Gomez', title: 'DevOps Manager', confidence: 'medium' },
    ],
  },
];

export const ProspectingReviewProspects = () => {
  const navigate = useNavigate();

  const companies = useMemo(() => mockCompanies, []);

  return (
    <ProspectingWizardLayout
      title="Prospecting — Review Prospects"
      primaryCtaText="Continue"
      activeStep="review-prospects"
      onPrimaryCta={() => navigate('/prospecting/wide/create')}
    >
      <ProspectsReviewTable companies={companies} />

      <div className="figma-wizard-bottom-cta figma-bottom-bar">
        <div className="figma-bottom-left">
          {/* UI-only: summary will be wired once API exists */}
          <span className="figma-muted">
            <strong>200 contacts</strong> from <strong>38 companies</strong> selected
          </span>
        </div>
        <Button
          type="primary"
          appearance="default"
          size="m"
          className="figma-primary-cta"
          onClick={() => navigate('/prospecting/wide/create')}
        >
          Continue
        </Button>
      </div>
    </ProspectingWizardLayout>
  );
};


