import { useNavigate } from 'react-router-dom';

interface BackButtonProps {
  to: string;
  label?: string;
}

export const BackButton = ({ to, label = 'Back' }: BackButtonProps) => {
  const navigate = useNavigate();

  return (
    <button
      className="back-button-component"
      onClick={() => navigate(to)}
    >
      ← {label}
    </button>
  );
};

