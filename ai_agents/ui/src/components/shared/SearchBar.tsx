import { useState } from 'react';
import type { FormEvent } from 'react';

interface SearchBarProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  onClear?: () => void;
  initialValue?: string;
}

export const SearchBar = ({
  placeholder = 'Search...',
  onSearch,
  onClear,
  initialValue = '',
}: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  const handleClear = () => {
    setQuery('');
    onClear?.();
  };

  return (
    <form onSubmit={handleSubmit} className="search-bar-component">
      <input
        type="text"
        className="search-bar-input"
        placeholder={placeholder}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button type="submit" className="search-bar-btn">
        Search
      </button>
      {query && onClear && (
        <button type="button" className="search-bar-clear-btn" onClick={handleClear}>
          Clear
        </button>
      )}
    </form>
  );
};

