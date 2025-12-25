import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Button, Typography } from 'novus';

export type ProspectingWizardStep = 'define-filters' | 'import-job' | 'review-prospects';

type Props = {
  title: string;
  primaryCtaText: string;
  onPrimaryCta: () => void;
  activeStep: ProspectingWizardStep;
  children: ReactNode;
};

export const ProspectingWizardLayout = ({
  title,
  primaryCtaText,
  onPrimaryCta,
  activeStep,
  children,
}: Props) => {
  const navigate = useNavigate();

  return (
    <div className="figma-wizard-page">
      <div className="figma-wizard-topbar">
        <div className="figma-wizard-topbar-left">
          <Button
            type="tertiary"
            appearance="default"
            size="s"
            className="figma-back-btn"
            onClick={() => navigate('/master-data/campaign')}
          >
            ← Back
          </Button>
        </div>
      </div>

      <div className="figma-wizard-titlebar">
        <div className="figma-wizard-titlebar-inner">
          <Typography variant="heading-xl" type="h1" className="figma-wizard-title">
            {title}
          </Typography>
          <Button
            type="primary"
            appearance="default"
            size="m"
            className="figma-primary-cta"
            onClick={onPrimaryCta}
          >
            {primaryCtaText}
          </Button>
        </div>
      </div>

      <div className="figma-wizard-body">
        <aside className="figma-wizard-nav">
          <div className="figma-wizard-nav-header">
            <Typography variant="heading-m" type="h2">
              Campaign Wizard
            </Typography>
            <Typography variant="body-s" type="p" className="figma-muted">
              Build your outbound campaign
            </Typography>
          </div>

          <div className="figma-wizard-nav-section">
            <div className="figma-wizard-nav-section-title">
              <span>Prospecting</span>
            </div>
            <div className="figma-wizard-nav-steps">
              <NavLink
                to="/prospecting/wide/define-filters"
                className={({ isActive }) =>
                  `figma-wizard-nav-step ${isActive || activeStep === 'define-filters' ? 'active' : ''}`
                }
              >
                <span className="figma-step-dot" />
                <span>Define filters</span>
              </NavLink>
              <NavLink
                to="/prospecting/wide/import-job"
                className={({ isActive }) =>
                  `figma-wizard-nav-step ${isActive || activeStep === 'import-job' ? 'active' : ''}`
                }
              >
                <span className="figma-step-dot" />
                <span>Import job</span>
              </NavLink>
              <NavLink
                to="/prospecting/wide/review-prospects"
                className={({ isActive }) =>
                  `figma-wizard-nav-step ${isActive || activeStep === 'review-prospects' ? 'active' : ''}`
                }
              >
                <span className="figma-step-dot" />
                <span>Review prospects</span>
              </NavLink>
            </div>
          </div>

          <div className="figma-wizard-nav-section figma-disabled">
            <div className="figma-wizard-nav-section-title">
              <span>Qualification</span>
            </div>
          </div>
          <div className="figma-wizard-nav-section figma-disabled">
            <div className="figma-wizard-nav-section-title">
              <span>Personalization</span>
            </div>
          </div>
          <div className="figma-wizard-nav-section figma-disabled">
            <div className="figma-wizard-nav-section-title">
              <span>Enrollment</span>
              <span className="figma-muted">0 enrolled</span>
            </div>
          </div>
        </aside>

        <section className="figma-wizard-content">{children}</section>
      </div>
    </div>
  );
};


