import { useState, useEffect, useMemo } from 'react';
import { API_BASE_URL } from '../../../config';
import './UnifiedQuestionnaire.scss';
import { ui } from '../../../i18n/ui';


interface FlowOption {
  value: string;
  label: string;
}

interface FlowQuestion {
  id: string;
  text: string;
  type: 'choice' | 'number' | 'boolean';
  options?: FlowOption[];
  risk_level?: string;
  show_if?: Record<string, any>;
  is_profile: boolean;
}


function shouldShow(question: FlowQuestion, answers: Record<string, any>): boolean {
  if (!question.show_if) return true;

  for (const [key, expected] of Object.entries(question.show_if)) {
    if (key === 'GENDER') {
      if (answers['GENDER'] !== expected) return false;
    } else if (key === 'HAS_OTHER_MEDS') {
      if (answers['HAS_OTHER_MEDS'] !== expected) return false;
    }
  }
  return true;
}

interface Props {
  substanceId: string;
  substanceName: string;
  onComplete: (
    result: 'green' | 'yellow' | 'orange' | 'red',
    explanation?: string,
    answers?: Record<string, any>,
    generalAdvice?: string[],
    hasCoverage?: boolean
  ) => void;
  onBack: () => void;
  lang: keyof typeof ui;
}

export const UnifiedQuestionnaire: React.FC<Props> = ({
  substanceId,
  substanceName,
  onComplete,
  onBack,
  lang,
}) => {
  const [allQuestions, setAllQuestions] = useState<FlowQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [redInterrupt, setRedInterrupt] = useState<string | null>(null);

  const t = (key: keyof typeof ui['fr']) => {
    return ui[lang][key] || ui['fr'][key];
  };

  useEffect(() => {
    const fetchFlow = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/automedication/flow/${substanceId}?lang=${lang}`
        );
        if (response.ok) {
          const data: FlowQuestion[] = await response.json();
          if (data.length === 0) {
            submitAnswers({});
            return;
          }
          setAllQuestions(data);
        }
      } catch (error) {
        console.error('Erreur chargement flux:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchFlow();
  }, [substanceId, lang]);

  const visibleQuestions = useMemo(() => {
    return allQuestions.filter((q) => shouldShow(q, answers));
  }, [allQuestions, answers]);
  const currentQuestion = visibleQuestions[currentIndex];
  const totalVisible = visibleQuestions.length;
  const progress = totalVisible > 0 ? ((currentIndex) / totalVisible) * 100 : 0;

  const submitAnswers = async (finalAnswers: Record<string, any>) => {
    setIsSubmitting(true);
    try {
      const medicalAnswers: Record<string, boolean> = {};
      for (const q of allQuestions) {
        if (!q.is_profile && finalAnswers[q.id] !== undefined) {
          medicalAnswers[q.id] = finalAnswers[q.id];
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/automedication/evaluate?lang=${lang}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cis: substanceId,
          answers: medicalAnswers,
          has_other_meds: finalAnswers['HAS_OTHER_MEDS'] ?? false,
          gender: finalAnswers['GENDER'] ?? null,
          age: finalAnswers['AGE'] ?? null,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        onComplete(
          result.score.toLowerCase() as 'green' | 'yellow' | 'orange' | 'red',
          result.ai_explanation,
          finalAnswers,
          result.general_advice || [],
          result.has_coverage ?? true
        );
      }
    } catch (error) {
      console.error('Erreur évaluation:', error);
      onComplete('red');
    }
  };

  const handleAnswer = (value: any) => {
    if (!currentQuestion) return;

    const newAnswers = { ...answers, [currentQuestion.id]: value };
    setAnswers(newAnswers);

    if (
      !currentQuestion.is_profile &&
      currentQuestion.risk_level === 'RED' &&
      value === true
    ) {
      setRedInterrupt(currentQuestion.text);
      submitAnswers(newAnswers);
      return;
    }

    const nextVisible = allQuestions.filter((q) => shouldShow(q, newAnswers));
    const nextIndex = currentIndex + 1;

    if (nextIndex >= nextVisible.length) {
      submitAnswers(newAnswers);
    } else {
      setCurrentIndex(nextIndex);
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    } else {
      onBack();
    }
  };


  if (isLoading) {
    return (
      <div className="unified-questionnaire">
        <div className="modern-loader-container">
          <div className="cube-loader"></div>
        </div>
      </div>
    );
  }

  if (redInterrupt || isSubmitting) {
    return (
      <div className="unified-questionnaire">
        <div className="interrupt-card">
          {redInterrupt ? (
            <>
              <div className="interrupt-icon">⛔</div>
              <h2>{t('score.risk.high')}</h2>
              <p>
                {t('score.risk.high.text').replace('{molecule}', substanceName)}
              </p>
              <div className="modern-loader-container">
                <div className="cube-loader"></div>
              </div>
            </>
          ) : (
            <>
              <div className="interrupt-icon">🔍</div>
              <h2>{t('search.loading')}</h2>
              <div className="modern-loader-container">
                <div className="cube-loader"></div>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return null;
  }

  return (
    <div className="unified-questionnaire">
      <div className="progress-bar">
        <div className="progress-bar__track">
          <div
            className="progress-bar__fill"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="progress-bar__label">
          {currentIndex + 1} / {totalVisible}
        </span>
      </div>

      <div className="drug-context">
        {t('questionnaire.about')} <strong>{substanceName}</strong>
      </div>

      <div className="question-card" key={currentQuestion.id}>
        <h3>{currentQuestion.text}</h3>

        {currentQuestion.type === 'choice' && currentQuestion.options && (
          <div className="options">
            {currentQuestion.options.map((opt) => (
              <button
                key={opt.value}
                className="option-btn"
                onClick={() => handleAnswer(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}


        {currentQuestion.type === 'boolean' && (
          <div className="options">
            <button className="option-btn" onClick={() => handleAnswer(true)}>
              {t('questionnaire.yes')}
            </button>
            <button className="option-btn" onClick={() => handleAnswer(false)}>
              {t('questionnaire.no')}
            </button>
          </div>
        )}
      </div>

      <div className="navigation">
        <button className="btn-back" onClick={handleBack}>
          ← {t('questionnaire.back')}
        </button>
      </div>
    </div>
  );
};
