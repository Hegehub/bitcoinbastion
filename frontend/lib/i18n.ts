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
    command: { openTrace: 'Open Trace', checkBitcoinAddress: 'Check Bitcoin Address', openMarketIntelligence: 'Open Market Intelligence', openTimeMachine: 'Open Time Machine' },
    accessibility: { skipToContent: 'Skip to content', mainNavigation: 'Main navigation', desktopNavigation: 'Desktop navigation', mobileNavigation: 'Mobile navigation' },
  },
  ru: {
    nav: {
      products: 'Продукты', developers: 'Разработчикам', selfHost: 'Самохостинг', manifesto: 'Манифест', evidence: 'Доказательства', status: 'Статус', roadmap: 'Дорожная карта', security: 'Безопасность', docs: 'Документация',
      platform: 'Платформа', citadel: 'Цитадель', trace: 'Трассировка', treasury: 'Казначейство', register: 'Регистрация', operations: 'Операции',
    },
    cta: { viewStatus: 'Показать статус', selfHostBastion: 'Самохостинг Bitcoin Bastion', menu: 'Меню', language: 'Язык' },
    footer: { product: 'Продукт', operators: 'Операторам', project: 'Проект', legalSafety: 'Право/Безопасность', advisoryOnly: 'Только рекомендации', noCustody: 'Без хранения средств' },
    command: { openTrace: 'Open Trace', checkBitcoinAddress: 'Check Bitcoin Address', openMarketIntelligence: 'Open Market Intelligence', openTimeMachine: 'Open Time Machine' },
    accessibility: { skipToContent: 'Перейти к содержимому', mainNavigation: 'Основная навигация', desktopNavigation: 'Навигация для десктопа', mobileNavigation: 'Мобильная навигация' },
  },
  es: {
    nav: {
      products: 'Productos', developers: 'Desarrolladores', selfHost: 'Autoalojado', manifesto: 'Manifiesto', evidence: 'Evidencia', status: 'Estado', roadmap: 'Hoja de ruta', security: 'Seguridad', docs: 'Documentación',
      platform: 'Plataforma', citadel: 'Ciudadela', trace: 'Trazado', treasury: 'Tesorería', register: 'Registro', operations: 'Operaciones',
    },
    cta: { viewStatus: 'Ver estado', selfHostBastion: 'Autoalojar Bitcoin Bastion', menu: 'Menú', language: 'Idioma' },
    footer: { product: 'Producto', operators: 'Operadores', project: 'Proyecto', legalSafety: 'Legal/Seguridad', advisoryOnly: 'Solo asesoramiento', noCustody: 'Sin custodia' },
    command: { openTrace: 'Open Trace', checkBitcoinAddress: 'Check Bitcoin Address', openMarketIntelligence: 'Open Market Intelligence', openTimeMachine: 'Open Time Machine' },
    accessibility: { skipToContent: 'Saltar al contenido', mainNavigation: 'Navegación principal', desktopNavigation: 'Navegación de escritorio', mobileNavigation: 'Navegación móvil' },
  },
  fr: {
    nav: {
      products: 'Produits', developers: 'Développeurs', selfHost: 'Auto-hébergement', manifesto: 'Manifeste', evidence: 'Preuves', status: 'Statut', roadmap: 'Feuille de route', security: 'Sécurité', docs: 'Documentation',
      platform: 'Plateforme', citadel: 'Citadelle', trace: 'Traçage', treasury: 'Trésorerie', register: 'Inscription', operations: 'Opérations',
    },
    cta: { viewStatus: 'Voir le statut', selfHostBastion: 'Auto-héberger Bitcoin Bastion', menu: 'Menu', language: 'Langue' },
    footer: { product: 'Produit', operators: 'Opérateurs', project: 'Projet', legalSafety: 'Légal/Sécurité', advisoryOnly: 'Conseil uniquement', noCustody: 'Sans garde' },
    command: { openTrace: 'Open Trace', checkBitcoinAddress: 'Check Bitcoin Address', openMarketIntelligence: 'Open Market Intelligence', openTimeMachine: 'Open Time Machine' },
    accessibility: { skipToContent: 'Aller au contenu', mainNavigation: 'Navigation principale', desktopNavigation: 'Navigation bureau', mobileNavigation: 'Navigation mobile' },
  },
  zh: {
    nav: {
      products: '产品', developers: '开发者', selfHost: '自托管', manifesto: '宣言', evidence: '证据', status: '状态', roadmap: '路线图', security: '安全', docs: '文档',
      platform: '平台', citadel: '堡垒', trace: '追踪', treasury: '资金库', register: '注册', operations: '运维',
    },
    cta: { viewStatus: '查看状态', selfHostBastion: '自托管 Bitcoin Bastion', menu: '菜单', language: '语言' },
    footer: { product: '产品', operators: '运维人员', project: '项目', legalSafety: '法律/安全', advisoryOnly: '仅供参考', noCustody: '不托管资金' },
    command: { openTrace: 'Open Trace', checkBitcoinAddress: 'Check Bitcoin Address', openMarketIntelligence: 'Open Market Intelligence', openTimeMachine: 'Open Time Machine' },
    accessibility: { skipToContent: '跳转到内容', mainNavigation: '主导航', desktopNavigation: '桌面导航', mobileNavigation: '移动导航' },
  },
  ja: {
    nav: {
      products: '製品', developers: '開発者', selfHost: 'セルフホスト', manifesto: 'マニフェスト', evidence: '証跡', status: 'ステータス', roadmap: 'ロードマップ', security: 'セキュリティ', docs: 'ドキュメント',
      platform: 'プラットフォーム', citadel: 'シタデル', trace: 'トレース', treasury: '財務', register: '登録', operations: '運用',
    },
    cta: { viewStatus: 'ステータスを見る', selfHostBastion: 'Bitcoin Bastionをセルフホスト', menu: 'メニュー', language: '言語' },
    footer: { product: '製品', operators: '運用者', project: 'プロジェクト', legalSafety: '法務/安全', advisoryOnly: '助言のみ', noCustody: 'カストディなし' },
    command: { openTrace: 'Open Trace', checkBitcoinAddress: 'Check Bitcoin Address', openMarketIntelligence: 'Open Market Intelligence', openTimeMachine: 'Open Time Machine' },
    accessibility: { skipToContent: 'コンテンツにスキップ', mainNavigation: 'メインナビゲーション', desktopNavigation: 'デスクトップナビゲーション', mobileNavigation: 'モバイルナビゲーション' },
  },
} as const;

export function isSupportedLanguage(value?: string | null): value is SiteLanguage {
  return Boolean(value && SUPPORTED_LANGUAGES.includes(value as SiteLanguage));
}

export function getLanguageFromCookie(value?: string | null): SiteLanguage {
  return isSupportedLanguage(value) ? value : 'en';
}


type HomeTranslations = {
  eyebrow: string;
  title: string;
  subtitle: string;
  readManifesto: string;
  selfHost: string;
};

export const PAGE_TRANSLATIONS: Record<SiteLanguage, { home: HomeTranslations; platform: { title: string; summary: string }; operations: { title: string; summary: string } }> = {
  en: {
    home: { eyebrow: 'Bitcoin-native infrastructure you can verify', title: 'Operator-controlled, no-custody Bitcoin infrastructure.', subtitle: 'Evidence over claims. Self-host capable. Built on a Bitcoin-first backend foundation with advisory-only workflows and transparent status signals.', readManifesto: 'Read Manifesto', selfHost: 'Self-host' },
    platform: { title: 'Platform', summary: 'This module page is an informational shell for Bitcoin Bastion platform orientation.' },
    operations: { title: 'Operations', summary: 'Kubernetes, GitOps, observability, evidence jobs, backup/restore and recovery drill foundations.' },
  },
  ru: {
    home: { eyebrow: 'Биткоин-нативная инфраструктура, которую можно проверить', title: 'Инфраструктура Bitcoin под контролем оператора и без хранения средств.', subtitle: 'Факты важнее заявлений. Готово к самохостингу. Построено на биткоин-ориентированной backend-основе с рекомендательными процессами и прозрачными статус-сигналами.', readManifesto: 'Читать манифест', selfHost: 'Самохостинг' },
    platform: { title: 'Платформа', summary: 'Эта страница модуля является информационной оболочкой для ориентации по платформе Bitcoin Bastion.' },
    operations: { title: 'Операции', summary: 'Основы Kubernetes, GitOps, наблюдаемости, задач доказательств, backup/restore и учений по восстановлению.' },
  },
  es: {
    home: { eyebrow: 'Infraestructura nativa de Bitcoin que puedes verificar', title: 'Infraestructura Bitcoin controlada por el operador y sin custodia.', subtitle: 'Evidencia sobre afirmaciones. Capaz de autoalojamiento. Construido sobre una base backend Bitcoin-first con flujos solo de asesoría y señales de estado transparentes.', readManifesto: 'Leer manifiesto', selfHost: 'Autoalojar' },
    platform: { title: 'Plataforma', summary: 'Esta página de módulo es una capa informativa para la orientación de la plataforma Bitcoin Bastion.' },
    operations: { title: 'Operaciones', summary: 'Fundamentos de Kubernetes, GitOps, observabilidad, trabajos de evidencia, copia/restauración y simulacros de recuperación.' },
  },
  fr: {
    home: { eyebrow: 'Infrastructure native Bitcoin que vous pouvez vérifier', title: 'Infrastructure Bitcoin contrôlée par l’opérateur, sans garde.', subtitle: 'Les preuves avant les promesses. Compatible auto-hébergement. Construite sur une base backend Bitcoin-first avec des workflows consultatifs et des signaux d’état transparents.', readManifesto: 'Lire le manifeste', selfHost: 'Auto-héberger' },
    platform: { title: 'Plateforme', summary: 'Cette page de module est une base informative pour l’orientation de la plateforme Bitcoin Bastion.' },
    operations: { title: 'Opérations', summary: 'Fondations Kubernetes, GitOps, observabilité, tâches de preuve, sauvegarde/restauration et exercices de reprise.' },
  },
  zh: {
    home: { eyebrow: '可验证的比特币原生基础设施', title: '由运营者掌控、非托管的比特币基础设施。', subtitle: '以证据为先，而非宣称。支持自托管。基于 Bitcoin-first 后端基础，提供仅建议型流程与透明状态信号。', readManifesto: '阅读宣言', selfHost: '自托管' },
    platform: { title: '平台', summary: '此模块页面是用于 Bitcoin Bastion 平台导览的信息壳层。' },
    operations: { title: '运维', summary: 'Kubernetes、GitOps、可观测性、证据任务、备份/恢复与恢复演练基础。' },
  },
  ja: {
    home: { eyebrow: '検証可能なBitcoinネイティブ基盤', title: '運用者が管理する、カストディ不要のBitcoinインフラ。', subtitle: '主張より証拠。セルフホスト対応。Bitcoin-firstなバックエンド基盤の上に、助言限定ワークフローと透明なステータス信号を構築。', readManifesto: 'マニフェストを読む', selfHost: 'セルフホスト' },
    platform: { title: 'プラットフォーム', summary: 'このモジュールページはBitcoin Bastionプラットフォーム案内のための情報シェルです。' },
    operations: { title: '運用', summary: 'Kubernetes、GitOps、可観測性、エビデンスタスク、バックアップ/復元、復旧訓練の基盤。' },
  },
};
