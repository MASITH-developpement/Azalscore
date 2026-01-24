/**
 * AZALSCORE - Module Template - Tests
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TemplateModule from '../index';

describe('TemplateModule', () => {
  it('should render without crashing', () => {
    render(<TemplateModule />);
    expect(screen.getByText(/Nom du Module/i)).toBeInTheDocument();
  });

  it('should display tabs', () => {
    render(<TemplateModule />);
    expect(screen.getByText(/Vue 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Vue 2/i)).toBeInTheDocument();
  });
});
