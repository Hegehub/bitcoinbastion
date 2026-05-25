import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { ReadinessWizard } from '@/components/selfhost/ReadinessWizard';

test('wizard recommends production when kubernetes is enabled', () => {
  render(<ReadinessWizard />);
  const select = screen.getByLabelText(/do you need kubernetes/i);
  fireEvent.change(select, { target: { value: 'yes' } });
  expect(screen.getByText(/recommended profile/i)).toBeTruthy();
  expect(screen.getByText('Production')).toBeTruthy();
});
