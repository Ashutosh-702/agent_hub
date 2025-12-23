interface LoaderProps {
  size?: 'small' | 'medium' | 'large';
  text?: string;
  fullScreen?: boolean;
}

export const Loader = ({ size = 'medium', text, fullScreen = false }: LoaderProps) => {
  const sizeClass = `loader-spinner-${size}`;
  
  if (fullScreen) {
    return (
      <div className="loader-fullscreen">
        <div className="loader-content">
          <div className={`loader-spinner ${sizeClass}`}></div>
          {text && <p className="loader-text">{text}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="loader-inline">
      <div className={`loader-spinner ${sizeClass}`}></div>
      {text && <p className="loader-text">{text}</p>}
    </div>
  );
};

