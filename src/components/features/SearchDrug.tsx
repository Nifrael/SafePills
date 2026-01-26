import React, { useState, useEffect } from 'react';
import { addDrug } from '../../lib/stores/medicationStore';

export interface Substance {
  substance_code: string;
  name: string;
  dose?: string;
}

export interface Drug {
  cis: string;
  name: string;
  substances: Substance[];
}

export const SearchDrug = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Drug[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const searchDrugs = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/search?q=${query}`);
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

  const handleSelect = (drug: Drug) => {
    addDrug(drug);
    setQuery('');
    setResults([]);
  };

  return (
    <div className="search-drug">
      <div className="search-drug__container">
        <input
          type="text"
          placeholder="Rechercher un médicament"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search-drug__input"
        />
        {isLoading && <div className="search-drug__loader">Chargement...</div>}
      </div>

      {results.length > 0 ? (
        <ul className="search-drug__results">
          {results.map((drug) => (
            <li
              key={drug.cis}
              onClick={() => handleSelect(drug)}
              className="search-drug__item"
            >
              <div className="search-drug__name">{drug.name}</div>
              <div className="search-drug__substances">
                {drug.substances.map(s => s.name).join(', ')}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        query.length >= 2 && !isLoading && (
          <div className="search-drug__no-results">
            Aucun médicament trouvé pour "{query}".
          </div>
        )
      )}
    </div>
  );
};

