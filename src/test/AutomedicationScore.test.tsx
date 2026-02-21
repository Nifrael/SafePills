/**
 * Tests unitaires pour AutomedicationScore.
 * Vérifie le rendu des différents niveaux de risque et l'intégration i18n.
 */
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AutomedicationScore } from '../components/features/automedication/AutomedicationScore';

describe('AutomedicationScore', () => {
  const defaultProps = {
    score: 'green' as const,
    molecule: 'Paracétamol',
    generalAdvice: [],
    hasCoverage: true,
    onReset: vi.fn(),
    lang: 'fr' as const,
  };

  it('affiche le label de risque FAIBLE pour un score green', () => {
    render(<AutomedicationScore {...defaultProps} />);
    expect(screen.getByText('FAIBLE RISQUE')).toBeInTheDocument();
  });

  it('affiche le label CONTRE-INDIQUÉ pour un score red', () => {
    render(<AutomedicationScore {...defaultProps} score="red" />);
    expect(screen.getByText('CONTRE-INDIQUÉ')).toBeInTheDocument();
  });

  it('affiche le nom de la molécule dans le texte de conseil', () => {
    render(<AutomedicationScore {...defaultProps} />);
    expect(screen.getByText(/Paracétamol/)).toBeInTheDocument();
  });

  it('affiche les conseils généraux quand fournis', () => {
    render(
      <AutomedicationScore
        {...defaultProps}
        generalAdvice={['Respectez la posologie', 'Ne pas dépasser 3g/jour']}
      />
    );
    expect(screen.getByText('Respectez la posologie')).toBeInTheDocument();
    expect(screen.getByText('Ne pas dépasser 3g/jour')).toBeInTheDocument();
  });

  it("affiche un avertissement quand le médicament n'est pas couvert", () => {
    render(<AutomedicationScore {...defaultProps} hasCoverage={false} />);
    expect(screen.getByText(/Notre base ne couvre pas/)).toBeInTheDocument();
  });

  it("n'affiche PAS l'avertissement quand le médicament est couvert", () => {
    render(<AutomedicationScore {...defaultProps} hasCoverage={true} />);
    expect(screen.queryByText(/Notre base ne couvre pas/)).not.toBeInTheDocument();
  });

  it("affiche l'explication IA quand fournie", () => {
    render(
      <AutomedicationScore
        {...defaultProps}
        score="orange"
        aiExplanation="Vous avez indiqué avoir des problèmes hépatiques..."
      />
    );
    expect(screen.getByText(/problèmes hépatiques/)).toBeInTheDocument();
    // Le disclaimer doit aussi apparaître
    expect(screen.getByText(/Intelligence Artificielle/)).toBeInTheDocument();
  });

  it("n'affiche PAS l'explication IA quand non fournie", () => {
    render(<AutomedicationScore {...defaultProps} />);
    expect(screen.queryByText(/Intelligence Artificielle/)).not.toBeInTheDocument();
  });

  it('appelle onReset quand le bouton est cliqué', () => {
    const mockReset = vi.fn();
    render(<AutomedicationScore {...defaultProps} onReset={mockReset} />);
    
    fireEvent.click(screen.getByText('Faire une autre évaluation'));
    expect(mockReset).toHaveBeenCalledOnce();
  });

  it('affiche les labels en espagnol quand lang=es', () => {
    render(<AutomedicationScore {...defaultProps} lang="es" score="red" />);
    expect(screen.getByText('CONTRAINDICADO')).toBeInTheDocument();
    expect(screen.getByText('Hacer otra evaluación')).toBeInTheDocument();
  });
});
