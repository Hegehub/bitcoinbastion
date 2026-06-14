import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { BastionCommandPalette, getTraceReportIdFromQuery } from '@/components/interactive/BastionCommandPalette';

function openPalette() {
  render(<BastionCommandPalette />);
  fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
  return screen.getByRole('dialog', { name: /bastion command palette/i });
}

test('command palette opens with ctrl+k', () => {
  openPalette();
  expect(screen.getByRole('dialog', { name: /bastion command palette/i })).toBeTruthy();
});

test('command palette exposes canonical Trace, platform, operations, and market actions', () => {
  const dialog = openPalette();

  const expected = [
    ['Open Trace', '/trace'],
    ['Check Bitcoin Address', '/check'],
    ['Open Platform', '/platform'],
    ['Open Operations', '/operations'],
    ['Open Evidence', '/evidence'],
    ['Open Status', '/status'],
    ['Open Developers', '/developers'],
    ['Open Docs', '/docs'],
    ['Open Security', '/security'],
    ['Open Roadmap', '/roadmap'],
    ['Open Console', '/console'],
    ['Open Market Intelligence', '/market'],
    ['Open Market Timeline', '/market/timeline'],
    ['Open Time Machine', '/market/time-machine'],
    ['Open Market Signals', '/market/signals'],
    ['Open Market Evidence', '/market/evidence'],
    ['Open Narratives', '/market/narratives'],
    ['Open Sources', '/market/sources'],
  ] as const;

  for (const [label, href] of expected) {
    expect(screen.getByRole('link', { name: new RegExp(label, 'i') }).getAttribute('href')).toBe(href);
  }

  expect(dialog.querySelector('a[href="/products"]')).toBeNull();
  expect(dialog.querySelector('a[href="/self-host"]')).toBeNull();
  expect(dialog.textContent).not.toContain('/trace/undefined');
  expect(dialog.textContent).not.toContain('/trace/{report_id}');
});

test('dynamic Trace report actions appear only for a valid report id query', () => {
  openPalette();

  expect(screen.queryByRole('link', { name: /open trace report/i })).toBeNull();
  expect(screen.queryByRole('link', { name: /open proof packet/i })).toBeNull();

  fireEvent.change(screen.getByPlaceholderText(/search pages or type a trace report id/i), { target: { value: '12345' } });

  expect(screen.getByRole('link', { name: /open trace report/i }).getAttribute('href')).toBe('/trace/12345');
  expect(screen.getByRole('link', { name: /open proof packet/i }).getAttribute('href')).toBe('/trace/12345/proof-packet');
  expect(document.body.textContent).not.toContain('/trace/undefined');
  expect(document.body.textContent).not.toContain('/trace/{report_id}');
});

test('dynamic Trace report actions reject unsafe or non-report-id queries', () => {
  openPalette();
  const input = screen.getByPlaceholderText(/search pages or type a trace report id/i);

  for (const query of ['trace/123', 'https://example.test/trace/123', 'xprv9s21ZrQH143K3', 'not-a-report']) {
    fireEvent.change(input, { target: { value: query } });
    expect(screen.queryByRole('link', { name: /open trace report/i })).toBeNull();
    expect(screen.queryByRole('link', { name: /open proof packet/i })).toBeNull();
  }
});

test('report id parser accepts only simple numeric ids', () => {
  expect(getTraceReportIdFromQuery(' 42 ')).toBe('42');
  expect(getTraceReportIdFromQuery('/42')).toBeNull();
  expect(getTraceReportIdFromQuery('https://example.test/42')).toBeNull();
  expect(getTraceReportIdFromQuery('xprv9s21ZrQH143K3')).toBeNull();
});

test('command palette avoids forbidden wording', () => {
  openPalette();
  const text = (document.body.textContent || '').toLowerCase();
  for (const bad of ['clean address', 'dirty address', 'criminal address', 'guaranteed safe', 'approved payment', 'verified illicit']) {
    expect(text.includes(bad)).toBe(false);
  }
});
