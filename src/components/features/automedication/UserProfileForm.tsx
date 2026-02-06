import React, { useState } from 'react';

export interface UserProfile {
  gender: 'M' | 'F' | null;
  age: number | null;
  hasOtherMeds: boolean;
}

interface Props {
  onComplete: (profile: UserProfile) => void;
  onBack: () => void;
}

export const UserProfileForm: React.FC<Props> = ({ onComplete, onBack }) => {
  const [gender, setGender] = useState<'M' | 'F' | null>(null);
  const [age, setAge] = useState<string>('');
  const [hasOtherMeds, setHasOtherMeds] = useState<boolean | null>(null);

  const handleSubmit = () => {
    const ageNumber = age ? parseInt(age, 10) : null;
    
    onComplete({
      gender,
      age: ageNumber,
      hasOtherMeds: hasOtherMeds ?? false
    });
  };

  const isValid = gender !== null && age.length > 0 && hasOtherMeds !== null;

  return (
    <div className="user-profile-form">
      <h2>Pour mieux vous conseiller</h2>
      <p className="subtitle">Répondez à ces quelques questions</p>

      <div className="form-section">
        <h3>Vous êtes :</h3>
        <div className="options">
          <button
            className={`option-btn ${gender === 'M' ? 'selected' : ''}`}
            onClick={() => setGender('M')}
          >
            👨 Un homme
          </button>
          <button
            className={`option-btn ${gender === 'F' ? 'selected' : ''}`}
            onClick={() => setGender('F')}
          >
            👩 Une femme
          </button>
        </div>
      </div>

      <div className="form-section">
        <h3>Votre âge :</h3>
        <div className="age-input-wrapper">
          <input
            type="number"
            min="1"
            max="120"
            placeholder="Ex: 35"
            value={age}
            onChange={(e) => setAge(e.target.value)}
          />
          <span className="age-label">ans</span>
        </div>
      </div>

      <div className="form-section">
        <h3>Prenez-vous actuellement d'autres médicaments de façon régulière ?</h3>
        <div className="options">
          <button
            className={`option-btn ${hasOtherMeds === true ? 'selected' : ''}`}
            onClick={() => setHasOtherMeds(true)}
          >
            ✓ Oui
          </button>
          <button
            className={`option-btn ${hasOtherMeds === false ? 'selected' : ''}`}
            onClick={() => setHasOtherMeds(false)}
          >
            ✗ Non
          </button>
        </div>
      </div>

      <div className="form-actions">
        <button
          className="btn-back"
          onClick={onBack}
        >
          ← Retour
        </button>
        <button
          className="btn-continue"
          onClick={handleSubmit}
          disabled={!isValid}
        >
          Continuer →
        </button>
      </div>
    </div>
  );
};
