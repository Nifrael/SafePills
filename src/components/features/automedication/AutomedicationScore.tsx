import React from 'react';
import './AutomedicationScore.scss';

interface Props {
  score: 'green' | 'orange' | 'red';
  molecule: string | null;
  aiExplanation?: string;
  generalAdvice: string[];
  hasCoverage: boolean;
  onReset: () => void;
}

export const AutomedicationScore: React.FC<Props> = ({
  score, molecule, aiExplanation, generalAdvice, hasCoverage, onReset
}) => {
  const getScoreData = () => {
    switch (score) {
      case 'green':
        return {
          label: 'FAIBLE RISQUE',
          text: `La prise de ${molecule} semble sûre dans votre situation. Respectez toujours les doses prescrites.`,
          class: 'score-green'
        };
      case 'orange':
        return {
          label: 'ATTENTION',
          text: `La prise de ${molecule} nécessite une vigilance particulière. Il est recommandé de demander l'avis de votre pharmacien.`,
          class: 'score-orange'
        };
      case 'red':
        return {
          label: 'DÉCONSEILLÉ',
          text: `La prise de ${molecule} est fortement déconseillée ou contre-indiquée dans votre situation. Consultez votre pharmacien ou médecin pour une alternative.`,
          class: 'score-red'
        };
    }
  };

  const data = getScoreData();

  return (
    <div className="automedication-score">
      <div className={`score-indicator ${data.class}`}>
        <span className="score-label">{data.label}</span>
      </div>
      
      <p className="advice">{data.text}</p>

      {/* P1-B : Avertissement si aucune question n'est associée */}
      {!hasCoverage && (
        <div className="no-coverage-warning">
          <span className="warning-icon">ℹ️</span>
          <p>
            Notre base ne couvre pas encore spécifiquement ce médicament.
            Ce résultat est indicatif. <strong>Demandez toujours conseil à votre pharmacien.</strong>
          </p>
        </div>
      )}

      {/* P1-A : Conseils généraux (affichés pour TOUS les scores) */}
      {generalAdvice.length > 0 && (
        <div className="general-advice-card">
          <h4>💊 Bon à savoir</h4>
          <ul>
            {generalAdvice.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Explication IA (ORANGE/RED uniquement) */}
      {aiExplanation && (
        <div className="ai-explanation-card">
          <h4>
            <span role="img" aria-label="pharmacist">👨‍⚕️</span> 
            L'analyse personnalisée de SafePills
          </h4>
          <p>{aiExplanation}</p>
          <small className="disclaimer">
            Explication générée par Intelligence Artificielle à titre indicatif. 
            Ne remplace pas l'avis d'un professionnel de santé.
          </small>
        </div>
      )}

      <button className="btn-reset" onClick={onReset}>Faire une autre évaluation</button>
    </div>
  );
};
