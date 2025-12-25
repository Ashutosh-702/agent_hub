import { useMemo, useState } from 'react';
import { Badge, Button, Input } from 'novus';

export type Confidence = 'high' | 'medium' | 'low';

export type ProspectContact = {
  id: string;
  name: string;
  title: string;
  confidence: Confidence;
};

export type ProspectCompany = {
  id: string;
  name: string;
  domain: string;
  region: string;
  size: string;
  contacts: ProspectContact[];
};

const confidenceBadge = (c: Confidence) => {
  if (c === 'high') return { state: 'success' as const, label: 'high confidence' };
  if (c === 'medium') return { state: 'neutral' as const, label: 'medium confidence' };
  return { state: 'warning' as const, label: 'low confidence' };
};

type Props = {
  companies: ProspectCompany[];
};

export const ProspectsReviewTable = ({ companies }: Props) => {
  const [tab, setTab] = useState<'company' | 'contact'>('company');
  const [query, setQuery] = useState('');
  const [expandedCompanyIds, setExpandedCompanyIds] = useState<Record<string, boolean>>({});
  const [selectedCompanyIds, setSelectedCompanyIds] = useState<Record<string, boolean>>({});
  const [selectedContactIds, setSelectedContactIds] = useState<Record<string, boolean>>({});

  const filteredCompanies = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return companies;
    return companies.filter(c => {
      const companyMatch = `${c.name} ${c.domain}`.toLowerCase().includes(q);
      const contactMatch = c.contacts.some(ct => `${ct.name} ${ct.title}`.toLowerCase().includes(q));
      return companyMatch || contactMatch;
    });
  }, [companies, query]);

  const toggleExpanded = (id: string) => {
    setExpandedCompanyIds(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleCompanySelected = (id: string, checked: boolean) => {
    setSelectedCompanyIds(prev => ({ ...prev, [id]: checked }));
    const company = companies.find(c => c.id === id);
    if (!company) return;
    setSelectedContactIds(prev => {
      const next = { ...prev };
      company.contacts.forEach(ct => {
        next[ct.id] = checked;
      });
      return next;
    });
  };

  const toggleContactSelected = (contactId: string, checked: boolean) => {
    setSelectedContactIds(prev => ({ ...prev, [contactId]: checked }));
  };

  const isCompanyChecked = (company: ProspectCompany) => {
    const explicit = selectedCompanyIds[company.id];
    if (explicit !== undefined) return explicit;
    // Infer from contacts
    const all = company.contacts.length > 0 && company.contacts.every(ct => selectedContactIds[ct.id]);
    return all;
  };

  const isCompanyIndeterminate = (company: ProspectCompany) => {
    const checkedCount = company.contacts.filter(ct => selectedContactIds[ct.id]).length;
    return checkedCount > 0 && checkedCount < company.contacts.length;
  };

  return (
    <div className="figma-review">
      <div className="figma-card">
        <div className="figma-inline-banner">
          <div className="figma-inline-banner-inner">
            <span className="figma-inline-banner-icon">ⓘ</span>
            <span>Select contacts to consider. You can view by contact or by company.</span>
          </div>
        </div>

        <div className="figma-review-toolbar">
          <div className="figma-review-search">
            <Input
              size="m"
              placeholder="Search name, title, company"
              value={query}
              onChange={(e: any) => setQuery(e.target.value)}
            />
          </div>
          <Button type="secondary" appearance="default" size="m">
            Filters
          </Button>
        </div>

        <div className="figma-tabs">
          <button
            type="button"
            className={`figma-tab ${tab === 'company' ? 'active' : ''}`}
            onClick={() => setTab('company')}
          >
            By Company
          </button>
          <button
            type="button"
            className={`figma-tab ${tab === 'contact' ? 'active' : ''}`}
            onClick={() => setTab('contact')}
          >
            By Contact
          </button>
        </div>

        {tab === 'contact' ? (
          <div className="figma-empty-slim">
            Contact view is coming soon (UI only right now).
          </div>
        ) : (
          <div className="figma-table-wrap">
            <div className="figma-table">
              <div className="figma-table-head">
                <div className="figma-th figma-th-check">
                  <input type="checkbox" aria-label="Select all" disabled />
                </div>
                <div className="figma-th">Company</div>
                <div className="figma-th figma-th-center">Contacts</div>
                <div className="figma-th figma-th-center">Region</div>
                <div className="figma-th">Size</div>
                <div className="figma-th figma-th-action" />
              </div>

              {filteredCompanies.map(company => {
                const expanded = !!expandedCompanyIds[company.id];
                const checked = isCompanyChecked(company);
                const indeterminate = isCompanyIndeterminate(company);

                return (
                  <div key={company.id} className="figma-row-group">
                    <div className="figma-tr">
                      <div className="figma-td figma-td-check">
                        <input
                          type="checkbox"
                          checked={checked}
                          ref={(el) => {
                            if (el) el.indeterminate = indeterminate;
                          }}
                          onChange={(e) => toggleCompanySelected(company.id, e.target.checked)}
                          aria-label={`Select ${company.name}`}
                        />
                      </div>
                      <div className="figma-td figma-td-company">
                        <div className="figma-company-cell">
                          <span className="figma-company-icon">🏢</span>
                          <div>
                            <div className="figma-company-name">{company.name}</div>
                            <div className="figma-company-domain">{company.domain}</div>
                          </div>
                        </div>
                      </div>
                      <div className="figma-td figma-td-center">
                        <Badge state="neutral" emphasis="subtle">
                          {company.contacts.length}
                        </Badge>
                      </div>
                      <div className="figma-td figma-td-center">
                        <Badge state="neutral" emphasis="subtle">
                          {company.region}
                        </Badge>
                      </div>
                      <div className="figma-td">{company.size}</div>
                      <div className="figma-td figma-td-action">
                        <Button
                          type="tertiary"
                          appearance="default"
                          size="s"
                          className="figma-row-action"
                          onClick={() => toggleExpanded(company.id)}
                        >
                          {expanded ? '▾' : '›'}
                        </Button>
                      </div>
                    </div>

                    {expanded && (
                      <div className="figma-expanded">
                        {company.contacts.map(ct => {
                          const c = confidenceBadge(ct.confidence);
                          return (
                            <div key={ct.id} className="figma-contact-row">
                              <div className="figma-contact-left">
                                <input
                                  type="checkbox"
                                  checked={!!selectedContactIds[ct.id]}
                                  onChange={(e) => toggleContactSelected(ct.id, e.target.checked)}
                                  aria-label={`Select ${ct.name}`}
                                />
                                <div>
                                  <div className="figma-contact-name">{ct.name}</div>
                                  <div className="figma-contact-title">{ct.title}</div>
                                </div>
                              </div>
                              <Badge state={c.state} emphasis="subtle">
                                {c.label}
                              </Badge>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}

              {filteredCompanies.length === 0 && (
                <div className="figma-empty-slim">No results</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


