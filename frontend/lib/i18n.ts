export const SUPPORTED_LANGUAGES = ['en', 'ru', 'es', 'fr', 'zh', 'ja'] as const;

export type SiteLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const LANGUAGE_COOKIE_NAME = 'bb_lang';

export const LANGUAGE_NAMES: Record<SiteLanguage, string> = {
  en: 'English',
  ru: 'Русский',
  es: 'Español',
  fr: 'Français',
  zh: '中文',
  ja: '日本語',
};

export const TRANSLATIONS = {
  en: {
    nav: {
      products: 'Products', developers: 'Developers', selfHost: 'Self-host', manifesto: 'Manifesto', evidence: 'Evidence', status: 'Status', roadmap: 'Roadmap', security: 'Security', docs: 'Docs',
      platform: 'Platform', citadel: 'Citadel', trace: 'Trace', treasury: 'Treasury', register: 'Register', operations: 'Operations',
    },
    cta: { viewStatus: 'View Status', selfHostBastion: 'Self-host Bitcoin Bastion', menu: 'Menu', language: 'Language' },
    footer: { product: 'Product', operators: 'Operators', project: 'Project', legalSafety: 'Legal/Safety', advisoryOnly: 'Advisory only', noCustody: 'No custody' },
    accessibility: { skipToContent: 'Skip to content', mainNavigation: 'Main navigation', desktopNavigation: 'Desktop navigation', mobileNavigation: 'Mobile navigation' },
  },
  ru: {
    nav: {
      products: 'Продукты', developers: 'Разработчикам', selfHost: 'Самохостинг', manifesto: 'Манифест', evidence: 'Доказательства', status: 'Статус', roadmap: 'Дорожная карта', security: 'Безопасность', docs: 'Документация',
      platform: 'Платформа', citadel: 'Цитадель', trace: 'Трассировка', treasury: 'Казначейство', register: 'Регистрация', operations: 'Операции',
    },
    cta: { viewStatus: 'Показать статус', selfHostBastion: 'Самохостинг Bitcoin Bastion', menu: 'Меню', language: 'Язык' },
    footer: { product: 'Продукт', operators: 'Операторам', project: 'Проект', legalSafety: 'Право/Безопасность', advisoryOnly: 'Только рекомендации', noCustody: 'Без хранения средств' },
    accessibility: { skipToContent: 'Перейти к содержимому', mainNavigation: 'Основная навигация', desktopNavigation: 'Навигация для десктопа', mobileNavigation: 'Мобильная навигация' },
  },
  es: {
    nav: {
      products: 'Productos', developers: 'Desarrolladores', selfHost: 'Autoalojado', manifesto: 'Manifiesto', evidence: 'Evidencia', status: 'Estado', roadmap: 'Hoja de ruta', security: 'Seguridad', docs: 'Documentación',
      platform: 'Plataforma', citadel: 'Ciudadela', trace: 'Trazado', treasury: 'Tesorería', register: 'Registro', operations: 'Operaciones',
    },
    cta: { viewStatus: 'Ver estado', selfHostBastion: 'Autoalojar Bitcoin Bastion', menu: 'Menú', language: 'Idioma' },
    footer: { product: 'Producto', operators: 'Operadores', project: 'Proyecto', legalSafety: 'Legal/Seguridad', advisoryOnly: 'Solo asesoramiento', noCustody: 'Sin custodia' },
    accessibility: { skipToContent: 'Saltar al contenido', mainNavigation: 'Navegación principal', desktopNavigation: 'Navegación de escritorio', mobileNavigation: 'Navegación móvil' },
  },
  fr: {
    nav: {
      products: 'Produits', developers: 'Développeurs', selfHost: 'Auto-hébergement', manifesto: 'Manifeste', evidence: 'Preuves', status: 'Statut', roadmap: 'Feuille de route', security: 'Sécurité', docs: 'Documentation',
      platform: 'Plateforme', citadel: 'Citadelle', trace: 'Traçage', treasury: 'Trésorerie', register: 'Inscription', operations: 'Opérations',
    },
    cta: { viewStatus: 'Voir le statut', selfHostBastion: 'Auto-héberger Bitcoin Bastion', menu: 'Menu', language: 'Langue' },
    footer: { product: 'Produit', operators: 'Opérateurs', project: 'Projet', legalSafety: 'Légal/Sécurité', advisoryOnly: 'Conseil uniquement', noCustody: 'Sans garde' },
    accessibility: { skipToContent: 'Aller au contenu', mainNavigation: 'Navigation principale', desktopNavigation: 'Navigation bureau', mobileNavigation: 'Navigation mobile' },
  },
  zh: {
    nav: {
      products: '产品', developers: '开发者', selfHost: '自托管', manifesto: '宣言', evidence: '证据', status: '状态', roadmap: '路线图', security: '安全', docs: '文档',
      platform: '平台', citadel: '堡垒', trace: '追踪', treasury: '资金库', register: '注册', operations: '运维',
    },
    cta: { viewStatus: '查看状态', selfHostBastion: '自托管 Bitcoin Bastion', menu: '菜单', language: '语言' },
    footer: { product: '产品', operators: '运维人员', project: '项目', legalSafety: '法律/安全', advisoryOnly: '仅供参考', noCustody: '不托管资金' },
    accessibility: { skipToContent: '跳转到内容', mainNavigation: '主导航', desktopNavigation: '桌面导航', mobileNavigation: '移动导航' },
  },
  ja: {
    nav: {
      products: '製品', developers: '開発者', selfHost: 'セルフホスト', manifesto: 'マニフェスト', evidence: '証跡', status: 'ステータス', roadmap: 'ロードマップ', security: 'セキュリティ', docs: 'ドキュメント',
      platform: 'プラットフォーム', citadel: 'シタデル', trace: 'トレース', treasury: '財務', register: '登録', operations: '運用',
    },
    cta: { viewStatus: 'ステータスを見る', selfHostBastion: 'Bitcoin Bastionをセルフホスト', menu: 'メニュー', language: '言語' },
    footer: { product: '製品', operators: '運用者', project: 'プロジェクト', legalSafety: '法務/安全', advisoryOnly: '助言のみ', noCustody: 'カストディなし' },
    accessibility: { skipToContent: 'コンテンツにスキップ', mainNavigation: 'メインナビゲーション', desktopNavigation: 'デスクトップナビゲーション', mobileNavigation: 'モバイルナビゲーション' },
  },
} as const;

export function isSupportedLanguage(value?: string | null): value is SiteLanguage {
  return Boolean(value && SUPPORTED_LANGUAGES.includes(value as SiteLanguage));
}

export function getLanguageFromCookie(value?: string | null): SiteLanguage {
  return isSupportedLanguage(value) ? value : 'en';
}
