# 🏰 Bitcoin Bastion

> **Суверенный интеллектуальный слой для Bitcoin**

---

## 🚀 Обзор

**Bitcoin Bastion** — это Bitcoin-native платформа интеллектуального анализа и операционных процессов, спроектированная для работы **поверх протокола Bitcoin**.

Она преобразует сырое состояние сети в:

- практические сигналы
- оценки рисков
- операционные решения
- инсайты о суверенности

---

> Большинство систем *потребляют данные Bitcoin*.  
> Bitcoin Bastion **интерпретирует реальность Bitcoin**.

---

## 🎯 Проблема

Пользователи Bitcoin, treasury-команды и операторы сталкиваются с фрагментированной средой:

- on-chain данные шумные и сложны для интерпретации  
- риски структуры кошельков невидимы  
- treasury-операции выполняются вручную и подвержены ошибкам  
- privacy-экспозиция плохо понятна  
- готовность к восстановлению редко проверяется  
- не существует единой системы для **гарантии суверенности**

---

## 💡 Решение

Bitcoin Bastion предоставляет единую систему, которая:

### 1. Понимает состояние Bitcoin
- on-chain активность  
- новости и нарративы  
- поведение сущностей  

### 2. Интерпретирует его
- генерация объяснимых сигналов  
- оценка рисков  
- контекстные рекомендации  

### 3. Даёт возможность действовать
- treasury-процессы  
- применение политик  
- операционная видимость  

### 4. Обеспечивает выживаемость (Citadel)
- готовность к восстановлению  
- картирование зависимостей  
- симуляция катастроф  
- планирование исправлений  

---

## 🧠 Архитектура системы

```text
Bitcoin Network (Protocol Layer)
        ↓
Data Ingestion
  - On-chain
  - News
  - Entities
        ↓
Interpretation Layer
  - Signal Engine
  - Explainability Graph
        ↓
Operational Layer
  - Wallet Intelligence
  - Treasury Engine
  - Policy Engine
  - Privacy Analysis
        ↓
Citadel Layer (Sovereignty)
  - Recovery
  - Dependencies
  - Simulations
  - Repair Plans
        ↓
Delivery Layer
  - API
  - Telegram
  - Operator Tools
````

---

## 🏰 Citadel — слой суверенности

Citadel — определяющий слой системы.

Он отвечает на критически важные вопросы:

* Можно ли восстановить ваш Bitcoin?
* Какие зависимости могут сломать вашу систему?
* Что произойдёт в условиях отказа?
* Что необходимо исправить немедленно?

---

> Bastion говорит вам, что происходит.
> Citadel говорит вам, переживёте ли вы это.

---

## ⚙️ Ключевые возможности

### Intelligence

* Сбор новостей и отслеживание репутации
* Генерация объяснимых сигналов
* Отслеживание сущностей и watchlists

### On-chain мониторинг

* Транзакционная активность
* Обнаружение крупных переводов
* Сигналы на основе событий

### Wallet & Treasury

* Оценка состояния кошелька
* Treasury request workflows
* Одобрения на основе политик

### Policy & Privacy

* Симуляция и применение политик
* Оценка privacy-рисков

### Observability

* Метрики и health probes
* Отслеживание задач и audit logs

### Sovereignty (Citadel)

* Scoring оценки
* Граф зависимостей
* Готовность к восстановлению
* Симуляции катастроф
* Проверка наследования
* Планы исправлений

---

## 🧰 Технологии

* **Backend**: FastAPI
* **Language**: Python 3.12
* **Database**: PostgreSQL
* **ORM**: SQLAlchemy 2.x
* **Queue**: Celery + Redis
* **Migrations**: Alembic
* **Auth**: JWT + Argon2
* **Metrics**: Prometheus
* **Telegram**: aiogram

---

## 📊 Roadmap и статус исполнения

> ✔ = Реализовано
> ❌ = Ещё не завершено

---

### 🧱 Foundation

* ✔ Модульный backend на FastAPI
* ✔ Модели базы данных и репозитории
* ✔ Система аутентификации (JWT)
* ✔ Middleware / logging / metrics
* ✔ Docker-инфраструктура
* ❌ Полное обеспечение консистентности миграций
* ❌ CI-level валидация схемы

---

### 📰 Intelligence Layer

* ✔ Сбор новостей
* ✔ Signal engine (baseline)
* ✔ Модели объяснимости
* ❌ Полная зрелость signal pipeline
* ❌ Глубина evidence graph

---

### ⛓ On-chain Layer

* ✔ Базовый on-chain ingestion
* ✔ Абстракция провайдера
* ❌ Интеграция с реальной Bitcoin-нодой
* ❌ Осведомлённость о состоянии цепи
* ❌ Моделирование reorg/finality

---

### 👛 Wallet & Treasury

* ✔ Оценка состояния кошелька
* ✔ Treasury workflows
* ✔ Policy engine
* ✔ Privacy scoring
* ❌ UTXO intelligence
* ❌ Descriptor awareness
* ❌ Spend simulation

---

### 🏰 Citadel (Sovereignty)

* ✔ Поверхность Citadel API
* ✔ Базовая оценка
* ✔ Endpoints восстановления и симуляций
* ❌ Персистентные модели суверенности
* ❌ Recovery proof engine
* ❌ Детерминированные симуляции
* ❌ Полный граф зависимостей
* ❌ Реальная scoring-система

---

### ⚡ Bitcoin-native Depth

* ❌ UTXO Engine
* ❌ Mempool Engine
* ❌ Моделирование fee market
* ❌ Script awareness
* ❌ Descriptor system
* ❌ Chain state engine

---

### 📡 Delivery & Ops

* ✔ Admin endpoints
* ✔ Отслеживание задач
* ✔ Observability snapshot
* ❌ Telegram runtime (full)
* ❌ Delivery orchestration
* ❌ Operator tooling

---

## 🧠 Принципы проектирования

### Bitcoin-native

Система построена на:

* UTXO-модели
* структуре транзакций
* динамике fee market
* script system

---

### Explainability-first

Все результаты должны:

* включать логику рассуждения
* показывать доказательства
* предоставлять confidence

---

### Sovereignty-first

Система исходит из того, что:

* нет custody
* нет доверия
* нет предположений о настройке пользователя

---

### Модульная эволюция

Каждый слой может развиваться независимо:

* ingestion
* signals
* policy
* Citadel

---

## 🔐 Модель безопасности

* Приватные ключи не хранятся
* Seed phrase не обрабатываются
* Аутентифицированный доступ к API
* Role-based access control (baseline)

---

## 🧪 Разработка

```bash
docker compose up --build
```

Документация:

```
http://localhost:8000/docs
```

Метрики:

```
http://localhost:8000/metrics
```

---

## 🚧 Статус

Bitcoin Bastion сейчас является:

* **сильной backend-платформой**
* **функциональной intelligence-системой**
* **ранней sovereignty engine**

Пока это ещё не:

* полностью Bitcoin-protocol-aware система
* полностью детерминированная система
* полностью production-hardened система

---

## 🧭 Видение

Bitcoin Bastion развивается в:

> Систему, которая понимает Bitcoin
>
> и гарантирует, что вы его переживёте.

---

## 
