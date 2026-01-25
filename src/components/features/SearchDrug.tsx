import React, { useState } from 'react';

interface SearchDrugProps {
  onAdd: (drugName: string) => void;
}

const SearchDrug: React.FC<SearchDrugProps> = ({ onAdd }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onAdd(query);
      setQuery('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-drug">
      <input
        type="text"
        placeholder="Rechercher un médicament"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="search-drug__input"
      />
      <button type="submit" className="search-drug__button">
        Ajouter
      </button>
    </form>
  );
};

export default SearchDrug;
