import React, { useState, useEffect, useMemo } from 'react';
import { API_BASE_URL } from '../../../config';
import './UnifiedQuestionnaire.scss';

// --- Types ---

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

interface Props {
  substanceId: string;
  substanceName: string;
  onComplete: (
    result: 'green' | 'orange' | 'red',
    explanation?: string,
    answers?: Record<string, any>,
    generalAdvice?: string[],
    hasCoverage?: boolean
  ) => void;
  onBack: () => void;
}

// --- Helpers ---

/**
 * Évalue si une question doit être affichée selon les réponses données.
 * Gère : GENDER exact match, AGE_MIN/AGE_MAX range, HAS_OTHER_MEDS boolean.
 */
function shouldShow(question: FlowQuestion, answers: Record<string, any>): boolean {
  if (!question.show_if) return true;

  for (const [key, expected] of Object.entries(question.show_if)) {
    if (key === 'GENDER') {
      if (answers['GENDER'] !== expected) return false;
    } else if (key === 'AGE_MIN') {
      const age = answers['AGE'];
      if (age !== undefined && age < expected) return false;
    } else if (key === 'AGE_MAX') {
      const age = answers['AGE'];
      if (age !== undefined && age > expected) return false;
    } else if (key === 'HAS_OTHER_MEDS') {
      if (answers['HAS_OTHER_MEDS'] !== expected) return false;
    }
  }
  return true;
}

// --- Component ---

export const UnifiedQuestionnaire: React.FC<Props> = ({
  substanceId,
  substanceName,
  onComplete,
  onBack,
}) => {
  const [allQuestions, setAllQuestions] = useState<FlowQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [ageInput, setAgeInput] = useState('');
  const [redInterrupt, setRedInterrupt] = useState<string | null>(null);

  // Charger le flux de questions au montage
  useEffect(() => {
    const fetchFlow = async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/automedication/flow/${substanceId}`
        );
        if (response.ok) {
          const data: FlowQuestion[] = await response.json();
          if (data.length === 0) {
            // Aucune question → appeler /evaluate quand même pour récupérer
            // les conseils généraux et le flag has_coverage
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
  }, [substanceId]);

  // Questions visibles selon les réponses données
  const visibleQuestions = useMemo(() => {
    return allQuestions.filter((q) => shouldShow(q, answers));
  }, [allQuestions, answers]);

  // Question courante
  const currentQuestion = visibleQuestions[currentIndex];
  const totalVisible = visibleQuestions.length;
  const progress = totalVisible > 0 ? ((currentIndex) / totalVisible) * 100 : 0;

  // --- Soumission du quiz ---
  const submitAnswers = async (finalAnswers: Record<string, any>) => {
    setIsSubmitting(true);
    try {
      // Séparer réponses profil et médicales
      const medicalAnswers: Record<string, boolean> = {};
      for (const q of allQuestions) {
        if (!q.is_profile && finalAnswers[q.id] !== undefined) {
          medicalAnswers[q.id] = finalAnswers[q.id];
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/automedication/evaluate`, {
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
          result.score.toLowerCase() as 'green' | 'orange' | 'red',
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

  // --- Handler de réponse ---
  const handleAnswer = (value: any) => {
    if (!currentQuestion) return;

    const newAnswers = { ...answers, [currentQuestion.id]: value };
    setAnswers(newAnswers);

    // Short-circuit RED : si réponse OUI à une question RED, on interrompt
    if (
      !currentQuestion.is_profile &&
      currentQuestion.risk_level === 'RED' &&
      value === true
    ) {
      setRedInterrupt(currentQuestion.text);
      submitAnswers(newAnswers);
      return;
    }

    // Recalculer les questions visibles avec les nouvelles réponses
    const nextVisible = allQuestions.filter((q) => shouldShow(q, newAnswers));
    const nextIndex = currentIndex + 1;

    if (nextIndex >= nextVisible.length) {
      // Toutes les questions ont été posées
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

  // --- Rendu : États spéciaux ---

  if (isLoading) {
    return (
      <div className="unified-questionnaire">
        <div className="loader">Préparation du questionnaire...</div>
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
              <h2>Risque important détecté</h2>
              <p>
                Nous avons identifié une contre-indication potentielle. Il n'est pas
                nécessaire de poursuivre le questionnaire.
              </p>
              <div className="loader">Analyse en cours...</div>
            </>
          ) : (
            <>
              <div className="interrupt-icon">🔍</div>
              <h2>Analyse en cours</h2>
              <div className="loader">Calcul du résultat...</div>
            </>
          )}
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return null;
  }

  // --- Rendu : Question ---

  return (
    <div className="unified-questionnaire">
      {/* Barre de progression */}
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

      {/* Contexte médicament */}
      <div className="drug-context">
        À propos de <strong>{substanceName}</strong>
      </div>

      {/* Carte question */}
      <div className="question-card" key={currentQuestion.id}>
        <h3>{currentQuestion.text}</h3>

        {/* Type: choice (ex: genre) */}
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

        {/* Type: number (ex: âge) */}
        {currentQuestion.type === 'number' && (
          <div className="number-input-area">
            <div className="age-input-wrapper">
              <input
                type="number"
                min="1"
                max="120"
                placeholder="Ex: 35"
                value={ageInput}
                onChange={(e) => setAgeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && ageInput) {
                    handleAnswer(parseInt(ageInput, 10));
                  }
                }}
                autoFocus
              />
              <span className="age-label">ans</span>
            </div>
            <button
              className="btn-continue"
              disabled={!ageInput}
              onClick={() => handleAnswer(parseInt(ageInput, 10))}
            >
              Continuer →
            </button>
          </div>
        )}

        {/* Type: boolean (oui/non) */}
        {currentQuestion.type === 'boolean' && (
          <div className="options">
            <button className="option-btn" onClick={() => handleAnswer(true)}>
              Oui
            </button>
            <button className="option-btn" onClick={() => handleAnswer(false)}>
              Non
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="navigation">
        <button className="btn-back" onClick={handleBack}>
          ← Retour
        </button>
      </div>
    </div>
  );
};
