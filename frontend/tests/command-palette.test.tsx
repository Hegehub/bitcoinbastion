import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { BastionCommandPalette } from '@/components/interactive/BastionCommandPalette';

test('command palette opens with ctrl+k', () => {
  render(<BastionCommandPalette />);
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
  expect(screen.getByRole('dialog', { name: /bastion command palette/i })).toBeTruthy();
});
