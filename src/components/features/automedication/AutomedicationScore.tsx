import './AutomedicationScore.scss';
import { ui } from '../../../i18n/ui';

interface Props {
  score: 'green' | 'yellow' | 'orange' | 'red';
  molecule: string | null;
  aiExplanation?: string;
  generalAdvice: string[];
  hasCoverage: boolean;
  onReset: () => void;
  lang: keyof typeof ui;
}

export const AutomedicationScore: React.FC<Props> = ({
  score, molecule, aiExplanation, generalAdvice, hasCoverage, onReset, lang
}) => {
  const t = (key: keyof typeof ui['fr']) => {
    return ui[lang][key] || ui['fr'][key];
  };

  const getScoreData = () => {
    switch (score) {
      case 'green':
        return {
          label: t('score.risk.low'),
          text: t('score.risk.low.text').replace('{molecule}', molecule || ''),
          class: 'score-green'
        };
      case 'yellow':
        return {
          label: t('score.risk.yellow'),
          text: t('score.risk.yellow.text').replace('{molecule}', molecule || ''),
          class: 'score-yellow'
        };
      case 'orange':
        return {
          label: t('score.risk.medium'),
          text: t('score.risk.medium.text').replace('{molecule}', molecule || ''),
          class: 'score-orange'
        };
      case 'red':
        return {
          label: t('score.risk.high'),
          text: t('score.risk.high.text').replace('{molecule}', molecule || ''),
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
          <p>{t('score.no_coverage.before')}<strong>{t('score.no_coverage.bold')}</strong></p>
        </div>
      )}

      {/* P1-A : Conseils généraux (affichés pour TOUS les scores) */}
      {generalAdvice.length > 0 && (
        <div className="general-advice-card">
          <h4>{t('score.general_advice')}</h4>
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
            {t('score.ai_explanation.title')}
          </h4>
          <p>{aiExplanation}</p>
          <small className="disclaimer">
            {t('score.ai_explanation.disclaimer')}
          </small>
        </div>
      )}

      <button className="btn-reset" onClick={onReset}>{t('score.reset')}</button>
    </div>
  );
};
