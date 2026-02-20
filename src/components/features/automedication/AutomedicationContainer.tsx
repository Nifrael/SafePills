import React, { useState } from 'react';
import { AutomedicationSearch } from './AutomedicationSearch';
import { UnifiedQuestionnaire } from './UnifiedQuestionnaire';
import { AutomedicationScore } from './AutomedicationScore';
import './Automedication.scss';

import { languages, defaultLang, ui } from '../../../i18n/ui';

interface Props {
  lang: keyof typeof ui;
}

export const AutomedicationContainer: React.FC<Props> = ({ lang = defaultLang }) => {
  const [step, setStep] = useState<'search' | 'questionnaire' | 'score'>('search');
  const [selectedSubstance, setSelectedSubstance] = useState<{
    code: string;
    name: string;
  } | null>(null);
  const [score, setScore] = useState<'green' | 'yellow' | 'orange' | 'red' | null>(null);
  const [aiExplanation, setAiExplanation] = useState<string | undefined>(undefined);
  const [generalAdvice, setGeneralAdvice] = useState<string[]>([]);
  const [hasCoverage, setHasCoverage] = useState<boolean>(true);

  const handleSelectMolecule = (substanceCode: string, substanceName: string) => {
    setSelectedSubstance({ code: substanceCode, name: substanceName });
    setStep('questionnaire');
  };

  const handleQuestionnaireComplete = (
    result: 'green' | 'yellow' | 'orange' | 'red',
    explanation?: string,
    answers?: Record<string, any>,
    advice?: string[],
    coverage?: boolean
  ) => {
    setScore(result);
    setAiExplanation(explanation);
    setGeneralAdvice(advice || []);
    setHasCoverage(coverage ?? true);
    setStep('score');
  };

  const handleReset = () => {
    setStep('search');
    setSelectedSubstance(null);
    setScore(null);
    setAiExplanation(undefined);
    setGeneralAdvice([]);
    setHasCoverage(true);
  };

  return (
    <div className="automedication-flow">
      {step === 'search' && (
        <AutomedicationSearch onSelect={handleSelectMolecule} lang={lang} />
      )}

      {step === 'questionnaire' && selectedSubstance && (
        <UnifiedQuestionnaire
          substanceId={selectedSubstance.code}
          substanceName={selectedSubstance.name}
          onComplete={handleQuestionnaireComplete}
          onBack={() => setStep('search')}
          lang={lang}
        />
      )}

      {step === 'score' && score && (
        <AutomedicationScore
          score={score}
          molecule={selectedSubstance?.name || null}
          aiExplanation={aiExplanation}
          generalAdvice={generalAdvice}
          hasCoverage={hasCoverage}
          onReset={handleReset}
          lang={lang}
        />
      )}
    </div>
  );
};
