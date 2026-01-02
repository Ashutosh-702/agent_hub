import React, { useState } from 'react';
import type { CampaignType } from './CampaignTypeSelection';

// Hardcoded products for now
const AVAILABLE_PRODUCTS = [
  { id: 'product-1', name: 'Fynd Platform', description: 'Complete e-commerce platform for enterprise brands' },
  { id: 'product-2', name: 'Fynd Store', description: 'Point-of-sale and retail store management solution' },
  { id: 'product-3', name: 'Fynd OMS', description: 'Omnichannel order management and fulfillment' },
  { id: 'product-4', name: 'Fynd WMS', description: 'AI-powered warehouse management system' },
  { id: 'product-5', name: 'Uniket', description: 'Unified commerce platform for D2C brands' },
  { id: 'product-6', name: 'Fynd Storefront', description: 'Headless commerce storefront builder' },
  { id: 'product-7', name: 'Fynd Marketplace', description: 'Multi-vendor marketplace solution' },
  { id: 'product-8', name: 'Fynd Analytics', description: 'Real-time commerce analytics and insights' },
];

export type ProductSelectionMode = 'manual' | 'ai';

interface ProductSelectionProps {
  campaignType: CampaignType;
  onComplete: (mode: ProductSelectionMode, selectedProducts: string[]) => void;
  onBack: () => void;
}

export const ProductSelection: React.FC<ProductSelectionProps> = ({
  campaignType,
  onComplete,
  onBack,
}) => {
  const [mode, setMode] = useState<ProductSelectionMode | null>(null);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);

  // AI mode is only available for single company funnel
  const isAiModeAvailable = campaignType === 'single_company';

  const handleProductToggle = (productId: string) => {
    setSelectedProducts((prev) =>
      prev.includes(productId)
        ? prev.filter((id) => id !== productId)
        : [...prev, productId]
    );
  };

  const handleSelectAll = () => {
    if (selectedProducts.length === AVAILABLE_PRODUCTS.length) {
      setSelectedProducts([]);
    } else {
      setSelectedProducts(AVAILABLE_PRODUCTS.map((p) => p.id));
    }
  };

  const handleContinue = () => {
    if (mode === 'ai') {
      onComplete('ai', []);
    } else if (mode === 'manual' && selectedProducts.length > 0) {
      onComplete('manual', selectedProducts);
    }
  };

  const canContinue = mode === 'ai' || (mode === 'manual' && selectedProducts.length > 0);

  return (
    <div className="product-selection">
      <div className="step-header">
        <h2>Select Products</h2>
        <p>Choose which products to pitch for this campaign</p>
      </div>

      {/* Mode Selection */}
      <div className="product-mode-selection">
        <button
          className={`mode-card ${mode === 'manual' ? 'selected' : ''}`}
          onClick={() => setMode('manual')}
        >
          <div className="mode-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </div>
          <h3>Manual Selection</h3>
          <p>Choose specific products to pitch</p>
          {mode === 'manual' && (
            <div className="selected-check">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          )}
        </button>

        <button
          className={`mode-card ${mode === 'ai' ? 'selected' : ''} ${!isAiModeAvailable ? 'disabled' : ''}`}
          onClick={() => isAiModeAvailable && setMode('ai')}
          disabled={!isAiModeAvailable}
        >
          <div className="mode-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
              <path d="M9 14v2"/>
              <path d="M15 14v2"/>
            </svg>
          </div>
          <h3>AI Decides</h3>
          <p>Let AI recommend the best products</p>
          {!isAiModeAvailable && (
            <span className="mode-unavailable">Only for Single Company</span>
          )}
          {mode === 'ai' && (
            <div className="selected-check">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            </div>
          )}
        </button>
      </div>

      {/* Manual Product Selection */}
      {mode === 'manual' && (
        <div className="product-list-section">
          <div className="product-list-header">
            <h3>Available Products</h3>
            <button className="select-all-btn" onClick={handleSelectAll}>
              {selectedProducts.length === AVAILABLE_PRODUCTS.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>
          <div className="product-list">
            {AVAILABLE_PRODUCTS.map((product) => (
              <label
                key={product.id}
                className={`product-item ${selectedProducts.includes(product.id) ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={selectedProducts.includes(product.id)}
                  onChange={() => handleProductToggle(product.id)}
                />
                <div className="product-checkbox">
                  {selectedProducts.includes(product.id) && (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  )}
                </div>
                <div className="product-info">
                  <span className="product-name">{product.name}</span>
                  <span className="product-desc">{product.description}</span>
                </div>
              </label>
            ))}
          </div>
          <div className="selected-count">
            {selectedProducts.length} product{selectedProducts.length !== 1 ? 's' : ''} selected
          </div>
        </div>
      )}

      {/* AI Mode Info */}
      {mode === 'ai' && (
        <div className="ai-mode-info">
          <div className="ai-info-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
          </div>
          <h3>AI Product Recommendation</h3>
          <p>
            Based on the company's profile, industry, and needs, our AI will automatically 
            recommend the most relevant products to pitch during the outreach phase.
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="step-actions">
        <button className="btn-secondary" onClick={onBack}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Back
        </button>
        <button 
          className="btn-primary btn-large" 
          onClick={handleContinue}
          disabled={!canContinue}
        >
          Continue
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default ProductSelection;

