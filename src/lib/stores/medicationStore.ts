import { atom, action } from 'nanostores';
import type { Drug } from '../../components/features/SearchDrug';

export const selectedDrugs = atom<Drug[]>([]);

export const addDrug = action(selectedDrugs, 'addDrug', (store, drug: Drug) => {
  const current = store.get();
  // On évite les doublons par CIS
  if (!current.find((d) => d.cis === drug.cis)) {
    store.set([...current, drug]);
  }
});

export const removeDrug = action(selectedDrugs, 'removeDrug', (store, cis: string) => {
  store.set(store.get().filter((d) => d.cis !== cis));
});

export const clearDrugs = action(selectedDrugs, 'clearDrugs', (store) => {
  store.set([]);
});
