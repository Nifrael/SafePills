import React, { useState } from 'react';

interface Question {
  id: string;
  text: string;
}

interface Props {
  id: string; // ID du médicament (CIS) ou substance
  molecule: string;
  onComplete: (result: 'green' | 'orange' | 'red') => void;
  onBack: () => void;
}

export const AutomedicationQuiz: React.FC<Props> = ({ id, molecule, onComplete, onBack }) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(true);

  // Charger les questions au montage
  React.useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/automedication/questions/${id}`);
        if (response.ok) {
          const data = await response.json();
          setQuestions(data);
        }
      } catch (error) {
        console.error('Erreur chargement questions:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchQuestions();
  }, [id]);

  const handleAnswer = (answer: boolean) => {
    const currentQ = questions[currentQuestionIndex];
    const newAnswers = { ...answers, [currentQ.id]: answer };
    setAnswers(newAnswers);

    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      submitAnswers(newAnswers);
    }
  };

  const submitAnswers = async (finalAnswers: Record<string, boolean>) => {
    try {
      setIsLoading(true);
      const response = await fetch('http://127.0.0.1:8000/api/automedication/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cis: id,
          answers: finalAnswers
        })
      });

      if (response.ok) {
        const result = await response.json();
        // result = { score: "GREEN" | "ORANGE" | "RED", details: [...] }
        onComplete(result.score.toLowerCase() as 'green' | 'orange' | 'red');
      }
    } catch (error) {
      console.error('Erreur calcul score:', error);
      // Fallback safe si erreur
      onComplete('red'); 
    }
  };

  if (isLoading) {
    return <div className="automedication-quiz"><div className="loader">Chargement...</div></div>;
  }

  if (questions.length === 0) {
    return (
      <div className="automedication-quiz">
        <h2>Pas de questions spécifiques pour {molecule}</h2>
        <div className="info-message">
           Ce médicament ne présente pas de contre-indications enregistrées dans notre base simplifiée.
        </div>
        <button className="btn-ok" onClick={() => onComplete('green')}>C'est noté</button>
      </div>
    );
  }

  const currentQ = questions[currentQuestionIndex];

  return (
    <div className="automedication-quiz">
      <h2>À propos de votre prise de <span>{molecule}</span></h2>
      
      <div className="question-card">
        <h3>{currentQ.text}</h3>
        <div className="options">
          <button onClick={() => handleAnswer(true)}>OUI</button>
          <button onClick={() => handleAnswer(false)}>NON</button>
        </div>
      </div>

      <div className="navigation">
        <button className="btn-back" onClick={onBack}>Retour</button>
        <span>Question {currentQuestionIndex + 1} / {questions.length}</span>
      </div>
    </div>
  );
};
