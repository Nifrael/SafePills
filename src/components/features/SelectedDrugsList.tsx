import React from 'react';
import { useStore } from '@nanostores/react';
import { selectedDrugs, removeDrug } from '../../lib/stores/medicationStore';

const SelectedDrugsList: React.FC = () => {
  const drugs = useStore(selectedDrugs);

  if (drugs.length === 0) {
    return <p className="drugs-list__empty">Aucun médicament sélectionné.</p>;
  }

  return (
    <div className="drugs-list">
      <ul className="drugs-list__container">
        {drugs.map((drug) => (
          <li key={drug.cis} className="drugs-list__item">
            <span className="drugs-list__name">{drug.name}</span>
            <button
              onClick={() => removeDrug(drug.cis)}
              className="drugs-list__remove"
              title="Supprimer"
            >
              &times;
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SelectedDrugsList;
