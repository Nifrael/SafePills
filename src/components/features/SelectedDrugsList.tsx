import React, { useState } from 'react';
import { useStore } from '@nanostores/react';
import { selectedDrugs, removeDrug } from '../../lib/stores/medicationStore';

// --- 1. DÉFINITION DES TYPES (Doit correspondre au Python) ---

interface InteractionResult {
  molecule_a: string;
  molecule_b: string;
  level_risk: string;     // ex: "Contre-indication"
  risk: string;
  management?: string;
}

interface SafePillsAnalysis {
  interaction_detected: boolean;
  global_severity: "Rouge" | "Orange" | "Jaune" | "Vert" | null;
  explanation: string;       // Le texte de l'IA
  conduct_to_follow: string; // Les conseils de l'IA
  technical_details: InteractionResult[];
}

export const SelectedDrugsList = () => {
  // On s'abonne au Store (Ordonnance virtuelle)
  const drugs = useStore(selectedDrugs);
  
  // États locaux pour l'interface
  const [analysis, setAnalysis] = useState<SafePillsAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // --- 2. FONCTION D'ANALYSE ---
  const handleAnalyze = async () => {
    if (drugs.length < 2) return;

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(drugs), // On envoie la liste brute
      });

      if (!response.ok) {
        throw new Error("Erreur de communication avec le serveur");
      }

      const data = await response.json();
      setAnalysis(data);

    } catch (err) {
      console.error(err);
      setError("Impossible de joindre l'IA. Vérifiez que le Backend tourne.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="selected-drugs-list">
      {/* 1. LISTE DES MÉDICAMENTS */}
      <div className="drugs-list">
        {drugs.length === 0 ? (
          <p className="drugs-list__empty">Aucun médicament sélectionné.</p>
        ) : (
          <ul className="drugs-list__container">
            {drugs.map((drug) => (
              <li key={drug.cis} className="drugs-list__item">
                <div className="drugs-list__info">
                  <span className="drugs-list__name">{drug.name}</span>
                </div>
                <button
                  onClick={() => removeDrug(drug.cis)}
                  className="drugs-list__remove"
                  title="Supprimer"
                >
                  &times;
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* 2. BOUTON D'ACTION */}
      <div className="action-area text-center">
        <button
          onClick={handleAnalyze}
          disabled={drugs.length < 2 || loading}
          className="action-area__button"
        >
          {loading ? 'Analyse en cours...' : '🔍 Analyser l\'ordonnance'}
        </button>
        
        {drugs.length < 2 && drugs.length > 0 && (
          <p className="action-area__hint action-area__hint--warning">
            Ajoutez un deuxième médicament pour vérifier les interactions.
          </p>
        )}
      </div>

      {/* 3. AFFICHAGE DES RÉSULTATS */}
      {error && <div className="analysis-error">{error}</div>}

      {analysis && (
        <div className={`analysis-result analysis-result--${analysis.global_severity?.toLowerCase() || 'default'}`}>
          
          <h3 className="analysis-result__title">
            {analysis.global_severity === 'Rouge' && '⛔'}
            {analysis.global_severity === 'Orange' && '⚠️'}
            {analysis.global_severity === 'Jaune' && '✋'}
            {analysis.global_severity === 'Vert' && '✅'}
            Analyse : Niveau {analysis.global_severity || 'Inconnu'}
          </h3>

          <div className="analysis-result__expert">
            <h4>L'avis de l'expert</h4>
            <p>{analysis.explanation}</p>
          </div>

          <div className="analysis-result__action">
            <h4>Conduite à tenir</h4>
            <p>{analysis.conduct_to_follow}</p>
          </div>

          {analysis.technical_details.length > 0 && (
            <div className="analysis-result__technical">
              <details>
                <summary>Détails techniques (Pharmacien)</summary>
                <ul>
                  {analysis.technical_details.map((detail, idx) => (
                    <li key={idx}>
                      <strong>{detail.molecule_a} + {detail.molecule_b}</strong> : 
                      <span> {detail.risk}</span>
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
