'use client';

import { useEffect } from 'react';
import { getPhraseDictionary, PHRASE_TRANSLATIONS } from '@/lib/phraseTranslations';
import type { SiteLanguage } from '@/lib/i18n';

const SKIPPED_TAGS = new Set(['CODE', 'PRE', 'SCRIPT', 'STYLE', 'TEXTAREA']);
const TRANSLATABLE_ATTRIBUTES = ['aria-label', 'title', 'placeholder', 'alt'] as const;

function normalizeText(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

function preserveOuterWhitespace(original: string, replacement: string): string {
  const leading = original.match(/^\s*/)?.[0] ?? '';
  const trailing = original.match(/\s*$/)?.[0] ?? '';
  return `${leading}${replacement}${trailing}`;
}

function buildReverseDictionary(): Map<string, string> {
  const reverse = new Map<string, string>();
  Object.values(PHRASE_TRANSLATIONS).forEach((dictionary) => {
    Object.entries(dictionary).forEach(([english, translated]) => {
      reverse.set(translated, english);
    });
  });
  return reverse;
}

function shouldSkipNode(node: Node): boolean {
  const element = node.nodeType === Node.ELEMENT_NODE ? node as Element : node.parentElement;
  return Boolean(element?.closest(Array.from(SKIPPED_TAGS).join(',')));
}

function translateTextValue(value: string, dictionary: Record<string, string>, reverse: Map<string, string>): string | null {
  const normalized = normalizeText(value);
  if (!normalized) return null;
  const english = reverse.get(normalized) ?? normalized;
  const translated = dictionary[english];
  return translated && translated !== normalized ? preserveOuterWhitespace(value, translated) : null;
}

function translateElementAttributes(element: Element, dictionary: Record<string, string>, reverse: Map<string, string>) {
  TRANSLATABLE_ATTRIBUTES.forEach((attribute) => {
    const value = element.getAttribute(attribute);
    if (!value) return;
    const translated = translateTextValue(value, dictionary, reverse);
    if (translated) element.setAttribute(attribute, translated.trim());
  });
}

function translateTree(root: ParentNode, dictionary: Record<string, string>, reverse: Map<string, string>) {
  if (!Object.keys(dictionary).length) return;

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  let current = walker.nextNode();

  while (current) {
    if (!shouldSkipNode(current)) {
      if (current.nodeType === Node.TEXT_NODE) {
        const translated = translateTextValue(current.nodeValue ?? '', dictionary, reverse);
        if (translated) current.nodeValue = translated;
      }
      if (current.nodeType === Node.ELEMENT_NODE) {
        translateElementAttributes(current as Element, dictionary, reverse);
      }
    }
    current = walker.nextNode();
  }
}

export function LanguageRuntimeTranslator({ language }: { language: SiteLanguage }) {
  useEffect(() => {
    const dictionary = getPhraseDictionary(language);
    if (!Object.keys(dictionary).length) return;

    const reverse = buildReverseDictionary();
    translateTree(document.body, dictionary, reverse);

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.TEXT_NODE) {
            const translated = translateTextValue(node.nodeValue ?? '', dictionary, reverse);
            if (translated) node.nodeValue = translated;
            return;
          }
          if (node.nodeType === Node.ELEMENT_NODE) {
            translateTree(node as Element, dictionary, reverse);
          }
        });
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [language]);

  return null;
}
