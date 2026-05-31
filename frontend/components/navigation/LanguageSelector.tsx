'use client';

import { useRouter } from 'next/navigation';
import { LANGUAGE_COOKIE_NAME, LANGUAGE_NAMES, SUPPORTED_LANGUAGES, type SiteLanguage } from '@/lib/i18n';

export function LanguageSelector({ value, label }: { value: SiteLanguage; label: string }) {
  const router = useRouter();

  return (
    <label className='flex items-center gap-2 text-sm text-bb-graphite'>
      <span className='sr-only'>{label}</span>
      <select
        aria-label={label}
        className='rounded-lg border border-bb-border bg-white px-2 py-1 text-sm'
        value={value}
        onChange={(event) => {
          document.cookie = `${LANGUAGE_COOKIE_NAME}=${event.target.value}; path=/; max-age=31536000; samesite=lax`;
          router.refresh();
        }}
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang} value={lang}>
            {LANGUAGE_NAMES[lang]}
          </option>
        ))}
      </select>
    </label>
  );
}
