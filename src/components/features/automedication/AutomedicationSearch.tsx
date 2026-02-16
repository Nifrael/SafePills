import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../../config';
import './AutomedicationSearch.scss';

interface SearchResult {
  id: string;
  type: 'drug' | 'substance';
  name: string;
  description?: string;
}

interface Props {
  onSelect: (id: string, name: string) => void;
}

export const AutomedicationSearch: React.FC<Props> = ({ onSelect }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const searchDrugs = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}`);
        if (response.ok) {
          const data = await response.json();
          setResults(data);
        }
      } catch (error) {
        console.error('Erreur lors de la recherche:', error);
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(searchDrugs, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (item: SearchResult) => {
    onSelect(item.id, item.name);
    setQuery('');
    setResults([]);
  };

  return (
    <div className="automedication-search">
      <h3>Quel médicament souhaitez-vous prendre ?</h3>
      <div className="search-input-wrapper">
        <input 
          type="text" 
          placeholder="Ex: Doliprane, Nurofen, Paracétamol..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        
        {isLoading && <div className="loader">Recherche...</div>}
        
        {results.length > 0 && (
          <ul className="suggestions-list">
            {results.map(item => (
              <li key={item.id} onClick={() => handleSelect(item)}>
                <div className="drug-name">{item.name}</div>
                <div className="substance-name">
                  {item.description || (item.type === 'drug' ? 'Médicament' : 'Substance')}
                </div>
              </li>
            ))}
          </ul>
        )}
        
        {query.length >= 2 && !isLoading && results.length === 0 && (
          <div className="no-results">
            Aucun médicament trouvé pour "{query}"
          </div>
        )}
      </div>
    </div>
  );
};
