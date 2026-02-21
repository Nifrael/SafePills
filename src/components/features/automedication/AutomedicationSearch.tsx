import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../../config';
import { ui } from '../../../i18n/ui';
import './AutomedicationSearch.scss';

interface SearchResult {
  id: string;
  type: 'drug' | 'substance';
  name: string;
  description?: string;
}

interface Props {
  onSelect: (id: string, name: string) => void;
  lang: keyof typeof ui;
}

export const AutomedicationSearch: React.FC<Props> = ({ onSelect, lang }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const t = (key: keyof typeof ui['fr']) => {
    return ui[lang][key] || ui['fr'][key];
  };

  useEffect(() => {
    const searchDrugs = async () => {
      if (query.length < 2) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}&lang=${lang}`);
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
  }, [query, lang]);

  const handleSelect = (item: SearchResult) => {
    onSelect(item.id, item.name);
    setQuery('');
    setResults([]);
  };

  return (
    <div className="automedication-search">
      <h3>{t('search.title')}</h3>
      <div className="search-input-wrapper">
        <input 
          type="text" 
          placeholder={t('search.placeholder.full')} 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        
        {isLoading && <div className="loader">{t('search.loading')}</div>}
        
        {results.length > 0 && (
          <ul className="suggestions-list">
            {results.map(item => (
              <li key={item.id} onClick={() => handleSelect(item)}>
                <div className="drug-name">{item.name}</div>
                <div className="substance-name">
                  {item.description || (item.type === 'drug' ? t('search.type.drug') : t('search.type.substance'))}
                </div>
              </li>
            ))}
          </ul>
        )}
        
        {query.length >= 2 && !isLoading && results.length === 0 && (
          <div className="no-results">
            {t('search.no_results').replace('{query}', query)}
          </div>
        )}
      </div>
    </div>
  );
};
