export interface StepperStep {
  id: string;
  title: string;
}

interface StepperProps {
  steps: StepperStep[];
  currentStep: string;
  onStepClick?: (stepId: string) => void;
  completedSteps?: string[];
}

export const Stepper = ({
  steps,
  currentStep,
  onStepClick,
  completedSteps = [],
}: StepperProps) => {
  const currentIndex = steps.findIndex((s) => s.id === currentStep);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0',
        padding: '1.5rem 2rem',
        background: 'var(--color-white)',
        borderRadius: '12px',
        border: '1px solid var(--color-gray-200)',
        marginBottom: '2rem',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
      }}
    >
      {steps.map((step, index) => {
        const isActive = step.id === currentStep;
        const isCompleted = completedSteps.includes(step.id) || index < currentIndex;
        const isClickable = onStepClick && (isCompleted || index === currentIndex);

        return (
          <div
            key={step.id}
            style={{
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <div
              onClick={() => isClickable && onStepClick?.(step.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                cursor: isClickable ? 'pointer' : 'default',
                opacity: !isActive && !isCompleted ? 0.5 : 1,
                transition: 'all 0.2s ease',
              }}
              role={isClickable ? 'button' : undefined}
              tabIndex={isClickable ? 0 : undefined}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: isActive
                    ? 'linear-gradient(135deg, var(--color-primary) 0%, #5558e3 100%)'
                    : isCompleted
                    ? 'var(--color-success)'
                    : 'var(--color-gray-200)',
                  color: isActive || isCompleted ? 'white' : 'var(--color-gray-500)',
                  transition: 'all 0.2s ease',
                  boxShadow: isActive ? '0 2px 8px rgba(46, 49, 190, 0.3)' : 'none',
                }}
              >
                {isCompleted ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              <span
                style={{
                  fontSize: '0.875rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? 'var(--color-gray-900)' : 'var(--color-gray-600)',
                  whiteSpace: 'nowrap',
                }}
              >
                {step.title}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                style={{
                  width: '48px',
                  height: '2px',
                  background: isCompleted ? 'var(--color-success)' : 'var(--color-gray-200)',
                  margin: '0 1rem',
                  borderRadius: '1px',
                  transition: 'background 0.2s ease',
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
};

