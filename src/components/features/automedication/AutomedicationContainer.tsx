import React, { useState } from 'react';
import { AutomedicationSearch } from './AutomedicationSearch';
import { AutomedicationQuiz } from './AutomedicationQuiz';
import { AutomedicationScore } from './AutomedicationScore';
import './Automedication.scss';

export const AutomedicationContainer: React.FC = () => {
  const [step, setStep] = useState<'search' | 'quiz' | 'score'>('search');
  const [selectedSubstance, setSelectedSubstance] = useState<{
    code: string;
    name: string;
  } | null>(null);
  const [score, setScore] = useState<'green' | 'orange' | 'red' | null>(null);

  const handleSelectMolecule = (substanceCode: string, substanceName: string) => {
    setSelectedSubstance({ code: substanceCode, name: substanceName });
    setStep('quiz');
  };

  const handleQuizComplete = (result: 'green' | 'orange' | 'red') => {
    setScore(result);
    setStep('score');
  };

  const handleReset = () => {
    setStep('search');
    setSelectedSubstance(null);
    setScore(null);
  };

  return (
    <div className="automedication-flow">
      {step === 'search' && (
        <AutomedicationSearch onSelect={handleSelectMolecule} />
      )}
      
      {step === 'quiz' && selectedSubstance && (
        <AutomedicationQuiz 
          id={selectedSubstance.code}
          molecule={selectedSubstance.name} 
          onComplete={handleQuizComplete}
          onBack={() => setStep('search')}
        />
      )}

      {step === 'score' && score && (
        <AutomedicationScore 
          score={score} 
          molecule={selectedSubstance?.name || null}
          onReset={handleReset}
        />
      )}
    </div>
  );
};
