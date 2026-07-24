import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders EQIP dashboard shell', () => {
  render(<App />);
  expect(screen.getByText(/Executive quality command center/i)).toBeInTheDocument();
});
