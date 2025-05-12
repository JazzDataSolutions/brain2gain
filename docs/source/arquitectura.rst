Arquitectura de la plataforma
===============================

El siguiente diagrama muestra la arquitectura de alto nivel de la plataforma:

.. mermaid::

   graph LR
     Browser[Usuario navegador]
     Traefik[Traefik (ingress)]
     Frontend[Vite · React “Landing + Store UI”]
     Backend[FastAPI · Python (API)]
     Postgres[(PostgreSQL)]
     CRM[API · módulo CRM]
     ERP[API · módulo ERP]
     Store[API · módulo Tienda]

     Browser --> Traefik
     Traefik --> Frontend
     Browser --> Traefik --> Backend
     Frontend --> Backend
     Backend --> Postgres
     CRM --> Postgres
     ERP --> Postgres
     Store --> Postgres

Cada componente puede escalar de forma independiente y se comunica mediante HTTP/REST. Traefik actúa como gateway y proxy inverso, gestionando rutas y certificados HTTPS.