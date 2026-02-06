import React, { useState } from 'react';
import { UserProfileForm } from './UserProfileForm';
import type { UserProfile } from './UserProfileForm';
import { AutomedicationSearch } from './AutomedicationSearch';
import { AutomedicationQuiz } from './AutomedicationQuiz';
import { AutomedicationScore } from './AutomedicationScore';
import './Automedication.scss';

export const AutomedicationContainer: React.FC = () => {
  const [step, setStep] = useState<'profile' | 'search' | 'quiz' | 'score'>('search');
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [selectedSubstance, setSelectedSubstance] = useState<{
    code: string;
    name: string;
  } | null>(null);
  const [score, setScore] = useState<'green' | 'orange' | 'red' | null>(null);

  const handleProfileComplete = (profile: UserProfile) => {
    setUserProfile(profile);
    setStep('quiz');
  };

  const handleSelectMolecule = (substanceCode: string, substanceName: string) => {
    setSelectedSubstance({ code: substanceCode, name: substanceName });
    setStep('profile');
  };

  const handleQuizComplete = (result: 'green' | 'orange' | 'red') => {
    setScore(result);
    setStep('score');
  };

  const handleReset = () => {
    setStep('search');
    setUserProfile(null);
    setSelectedSubstance(null);
    setScore(null);
  };

  return (
    <div className="automedication-flow">
      {step === 'search' && (
        <AutomedicationSearch onSelect={handleSelectMolecule} />
      )}

      {step === 'profile' && (
        <UserProfileForm 
          onComplete={handleProfileComplete} 
          onBack={() => setStep('search')}
        />
      )}
      
      {step === 'quiz' && selectedSubstance && userProfile && (
        <AutomedicationQuiz 
          id={selectedSubstance.code}
          molecule={selectedSubstance.name} 
          userProfile={userProfile}
          onComplete={handleQuizComplete}
          onBack={() => setStep('profile')}
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
