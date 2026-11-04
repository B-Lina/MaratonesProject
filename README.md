# Sistema de Optimización de Rutas de Salud Rural Dispersa

Sistema escalable y desacoplado diseñado para la priorización y optimización logística de atención médica en sectores rurales. La solución combina un microservicio heurístico de alto rendimiento con un orquestador seguro y un panel web interactivo.

---

## 🏗️ Arquitectura del Sistema

El sistema implementa una arquitectura orientada a servicios (SOA / Cloud-Native) estructurada en tres capas independientes:

```text
[ Frontend (HTML/JS + Firebase Auth) ] 
                 │
                 │ (Peticiones HTTPS + Bearer Token)
                 ▼
 [ Orquestador Backend (Django REST Framework) ]
                 │
                 │ (Comunicación Interna REST)
                 ▼
  [ Microservicio Heurístico (FastAPI) ] ──► [ Persistencia & Auditoría (Firestore) ]
