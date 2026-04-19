# 🏰 Bitcoin Bastion

> **Capa de inteligencia soberana para Bitcoin**

---

## 🚀 Descripción general

**Bitcoin Bastion** es una plataforma de inteligencia y operaciones nativa de Bitcoin, diseñada para funcionar **sobre el protocolo Bitcoin**.

Transforma el estado bruto de la red en:

- señales accionables
- evaluaciones de riesgo
- decisiones operativas
- información sobre soberanía

---

> La mayoría de los sistemas *consumen datos de Bitcoin*.  
> Bitcoin Bastion **interpreta la realidad de Bitcoin**.

---

## 🎯 Problema

Los usuarios de Bitcoin, las tesorerías y los operadores se enfrentan a un entorno fragmentado:

- los datos on-chain son ruidosos y difíciles de interpretar  
- los riesgos de la estructura de las wallets son invisibles  
- las operaciones de tesorería son manuales y propensas a errores  
- la exposición de privacidad se comprende de forma deficiente  
- la preparación para la recuperación rara vez se verifica  
- no existe un sistema unificado para la **garantía de soberanía**

---

## 💡 Solución

Bitcoin Bastion proporciona un sistema unificado que:

### 1. Comprende el estado de Bitcoin
- actividad on-chain  
- noticias y narrativas  
- comportamiento de entidades  

### 2. Lo interpreta
- generación de señales explicables  
- puntuación de riesgo  
- recomendaciones contextuales  

### 3. Permite actuar
- flujos de trabajo de tesorería  
- aplicación de políticas  
- visibilidad operativa  

### 4. Garantiza la supervivencia (Citadel)
- preparación para la recuperación  
- mapeo de dependencias  
- simulación de desastres  
- planificación de reparaciones  

---

## 🧠 Arquitectura del sistema

```text
Red Bitcoin (Capa de protocolo)
        ↓
Ingesta de datos
  - On-chain
  - Noticias
  - Entidades
        ↓
Capa de interpretación
  - Motor de señales
  - Grafo de explicabilidad
        ↓
Capa operativa
  - Inteligencia de wallets
  - Motor de tesorería
  - Motor de políticas
  - Análisis de privacidad
        ↓
Capa Citadel (Soberanía)
  - Recuperación
  - Dependencias
  - Simulaciones
  - Planes de reparación
        ↓
Capa de entrega
  - API
  - Telegram
  - Herramientas para operadores
```

---

## 🏰 Citadel — Capa de soberanía

Citadel es la capa definitoria del sistema.

Responde a preguntas críticas:

* ¿Puede recuperarse tu Bitcoin?
* ¿Qué dependencias pueden romper tu sistema?
* ¿Qué ocurre bajo condiciones de fallo?
* ¿Qué debe corregirse inmediatamente?

---

> Bastion te dice qué está ocurriendo.
> Citadel te dice si sobrevives a ello.

---

## ⚙️ Capacidades principales

### Inteligencia

* Ingesta de noticias y seguimiento de reputación
* Generación de señales explicables
* Seguimiento de entidades y listas de vigilancia

### Monitoreo on-chain

* Actividad de transacciones
* Detección de grandes transferencias
* Señales basadas en eventos

### Wallet y tesorería

* Evaluación de la salud de la wallet
* Flujos de solicitud de tesorería
* Aprobaciones basadas en políticas

### Políticas y privacidad

* Simulación y aplicación de políticas
* Puntuación de riesgo de privacidad

### Observabilidad

* Métricas y comprobaciones de salud
* Seguimiento de trabajos y registros de auditoría

### Soberanía (Citadel)

* Puntuación de evaluaciones
* Grafo de dependencias
* Preparación para la recuperación
* Simulaciones de desastres
* Verificación de herencia
* Planes de reparación

---

## 🧰 Tecnología

* **Backend**: FastAPI
* **Lenguaje**: Python 3.12
* **Base de datos**: PostgreSQL
* **ORM**: SQLAlchemy 2.x
* **Cola**: Celery + Redis
* **Migraciones**: Alembic
* **Autenticación**: JWT + Argon2
* **Métricas**: Prometheus
* **Telegram**: aiogram

---

## 📊 Roadmap y estado de ejecución

> ✔ = Implementado
> ❌ = Aún no completado

---

### 🧱 Fundamentos

* ✔ Backend modular con FastAPI
* ✔ Modelos de base de datos y repositorios
* ✔ Sistema de autenticación (JWT)
* ✔ Middleware / logging / métricas
* ✔ Infraestructura Docker
* ❌ Aplicación completa de consistencia de migraciones
* ❌ Validación de esquema a nivel de CI

---

### 📰 Capa de inteligencia

* ✔ Ingesta de noticias
* ✔ Motor de señales (base)
* ✔ Modelos de explicabilidad
* ❌ Madurez completa del pipeline de señales
* ❌ Profundidad del grafo de evidencias

---

### ⛓ Capa on-chain

* ✔ Base de ingesta on-chain
* ✔ Abstracción de proveedores
* ❌ Integración real con un nodo Bitcoin
* ❌ Conciencia del estado de la cadena
* ❌ Modelado de reorganizaciones/finalidad

---

### 👛 Wallet y tesorería

* ✔ Evaluación de la salud de la wallet
* ✔ Flujos de trabajo de tesorería
* ✔ Motor de políticas
* ✔ Puntuación de privacidad
* ❌ Inteligencia UTXO
* ❌ Conciencia de descriptores
* ❌ Simulación de gasto

---

### 🏰 Citadel (Soberanía)

* ✔ Superficie API de Citadel
* ✔ Base de evaluación
* ✔ Endpoints de recuperación y simulación
* ❌ Modelos persistentes de soberanía
* ❌ Motor de prueba de recuperación
* ❌ Simulaciones deterministas
* ❌ Grafo completo de dependencias
* ❌ Sistema real de puntuación

---

### ⚡ Profundidad nativa de Bitcoin

* ❌ Motor UTXO
* ❌ Motor de mempool
* ❌ Modelado del mercado de comisiones
* ❌ Conciencia de scripts
* ❌ Sistema de descriptores
* ❌ Motor de estado de cadena

---

### 📡 Entrega y operaciones

* ✔ Endpoints de administración
* ✔ Seguimiento de trabajos
* ✔ Snapshot de observabilidad
* ❌ Runtime completo de Telegram
* ❌ Orquestación de entrega
* ❌ Herramientas para operadores

---

## 🧠 Principios de diseño

### Nativo de Bitcoin

El sistema se construye sobre:

* modelo UTXO
* estructura de transacciones
* dinámica del mercado de comisiones
* sistema de scripts

---

### Explicabilidad primero

Todas las salidas deben:

* incluir razonamiento
* mostrar evidencia
* proporcionar confianza

---

### Soberanía primero

El sistema asume:

* sin custodia
* sin confianza
* sin suposiciones sobre la configuración del usuario

---

### Evolución modular

Cada capa puede evolucionar de forma independiente:

* ingesta
* señales
* políticas
* Citadel

---

## 🔐 Modelo de seguridad

* No se almacenan claves privadas
* No se gestionan frases semilla
* Acceso API autenticado
* Control de acceso basado en roles (base)

---

## 🧪 Desarrollo

```bash
docker compose up --build
```

Documentación:

```text
http://localhost:8000/docs
```

Métricas:

```text
http://localhost:8000/metrics
```

---

## 🚧 Estado

Bitcoin Bastion es actualmente:

* una **plataforma backend sólida**
* un **sistema de inteligencia funcional**
* un **motor de soberanía en etapa temprana**

Aún no es:

* plenamente consciente del protocolo Bitcoin
* plenamente determinista
* plenamente endurecido para producción

---

## 🧭 Visión

Bitcoin Bastion evoluciona hacia:

> Un sistema que entiende Bitcoin
>
> y garantiza que sobrevivas a él.

---

## 
