import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SearchDrug from './SearchDrug';

describe('SearchDrug Component', () => {
  it('renders the input field', () => {
    render(<SearchDrug onAdd={() => {}} />);
    const input = screen.getByPlaceholderText(/rechercher un médicament/i);
    expect(input).toBeInTheDocument();
  });

  it('calls onAdd when submitting a valid drug name', () => {
    const mockOnAdd = vi.fn();
    render(<SearchDrug onAdd={mockOnAdd} />);

    const input = screen.getByPlaceholderText(/rechercher un médicament/i);
    const button = screen.getByRole('button', { name: /ajouter/i });

    fireEvent.change(input, { target: { value: 'Doliprane' } });
    fireEvent.click(button);

    expect(mockOnAdd).toHaveBeenCalledTimes(1);
    expect(mockOnAdd).toHaveBeenCalledWith('Doliprane');
  });

  it('does not call onAdd if input is empty', () => {
    const mockOnAdd = vi.fn();
    render(<SearchDrug onAdd={mockOnAdd} />);

    const button = screen.getByRole('button', { name: /ajouter/i });
    fireEvent.click(button);

    expect(mockOnAdd).not.toHaveBeenCalled();
  });
});
