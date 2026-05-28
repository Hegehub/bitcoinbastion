'use client';

import { useEffect, useState } from 'react';
import { getLanguageFromCookie, isSupportedLanguage, LANGUAGE_COOKIE_NAME, type SiteLanguage } from '@/lib/i18n';

export function useRuntimeLanguage(defaultLanguage: SiteLanguage = 'en'): SiteLanguage {
  const [language, setLanguage] = useState<SiteLanguage>(defaultLanguage);

  useEffect(() => {
    const htmlLang = typeof document !== 'undefined' ? document.documentElement.lang : defaultLanguage;
    if (isSupportedLanguage(htmlLang)) {
      setLanguage(htmlLang);
      return;
    }
    const cookieValue = typeof document !== 'undefined'
      ? document.cookie.split('; ').find((row) => row.startsWith(`${LANGUAGE_COOKIE_NAME}=`))?.split('=')[1]
      : undefined;
    setLanguage(getLanguageFromCookie(cookieValue));
  }, [defaultLanguage]);

  return language;
}
