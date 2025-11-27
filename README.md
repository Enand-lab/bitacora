<p align="center">
  <img src="static/icons/logo-derrotero.png" alt="Logo Diario de Bitácora" width="120">
</p>

# Cuaderno de Bitácora

[English version](docs/en/README.md)

> *Un diario de a bordo offline-first, hecho para navegantes que escriben con el corazón y navegan con datos.*

**Cuaderno de bitácora** es autónomo, ligero y pensado para funcionar incluso cuando el horizonte no tiene señal.  
Puede vivir solo —y lo hace muy bien—, pero si le presentas a **Signal K**, se enamora al instante 😊.

---

### Una relación especial con Signal K

Aunque **funciona completamente sin conexión**, Cuaderno de Bitácora cobra una dimensión extra si compartes tu viaje con un servidor Signal K:

- Al escribir una nota, **puede registrar automáticamente** la posición, el rumbo, la velocidad del viento, el estado del mar… *lo que tu sistema esté enviando*.
- Puedes configurarla para que **publique cada entrada (o solo las que elijas)** en el recurso `notes` de Signal K.
- Esas notas aparecerán luego en herramientas como **Freeboard, KIP o cualquier interfaz compatible**, como si las hubieras añadido directamente desde allí.

> En resumen: si Signal K está a bordo, Diario de Bitácora no solo guarda tus palabras… también el **contexto del momento en que las escribiste**.

---

### Un proyecto personal, hecho desde la cubierta

Este cuaderno nació de una necesidad real: **yo lo uso a bordo**.  
No es un producto comercial, ni pretende ser 100% configurable para todos los gustos. Es sencillo, funcional y sincero.

**¿Qué puedes esperar?**
- Una herramienta **útil y autónoma** para registrar tu navegación.
- **Posibles fallos o errores**, porque está en evolución (¡y el mar enseña humildad!).
- Actualizaciones lentas, pero **hechas con cuidado**.

Si buscas perfección absoluta, quizás no sea para ti.  
Pero si buscas un compañero de bitácora fiel, que respeta tu privacidad y funciona sin internet… bienvenido/a.

---

### No es una app móvil… pero sí para móviles

Diario de Bitácora **no es una aplicación nativa para Android o iOS**.  
Es un **servidor web ligero**, pensado para instalarse en una **Raspberry Pi**, un NUC, o cualquier sistema Linux en tu red local.

Sin embargo:
- Está **diseñado mobile-first**: se ve y se usa muy bien desde el móvil.
- Puedes acceder desde cualquier navegador en la red del barco: `http://bitacora.local:5000`.
- Incluso puedes **instalarlo como PWA** (Progressive Web App) en tu dispositivo.

---

### Automatización y API

¿Quieres integrar Diario de Bitácora con **Node-RED**, scripts personalizados o sistemas externos?  
Disponemos de una **API REST ligera** para crear, consultar, editar o borrar entradas, e incluso generar copias de seguridad desde otro sistema.

➡️ **Documentación completa de la API**: [docs/es/api.md](docs/es/api.md)

---

### Instalación

Usamos un **script de instalación sencillo** (`install.sh`) que configura todo automáticamente en tu Raspberry Pi o Linux: entorno virtual, servicio systemd, nombre `.local`, directorios de datos, etc.

➡️ **Guía detallada de instalación**: [docs/es/instalacion.md](docs/es/instalacion.md)

---

## Capturas de pantalla


<p align="center">
  <img src="static/images/lista-entradas.jpg" alt="Lista de entradas" width="48%">
  <img src="static/images/nueva-entrada.jpg" alt="Nueva entrada" width="48%">
</p>

<p align="center">
  <img src="static/images/ver-entrada.jpg" alt="Vista de entrada" width="48%">
  <img src="static/images/configuracion.jpg" alt="Configuración" width="48%">
</p>

---

### Agradecimientos

- **Iconos**: [Lucide](https://lucide.dev), bajo licencia ISC.
- **Estilos**: [Pico.css](https://picocss.com), por demostrar que menos es más.
- **Signal K**: por hacer que los datos de navegación sean libres y abiertos.

---

> *“La bitácora no miente. Guarda lo que fuiste, lo que viste, y lo que soñaste mientras el barco cortaba el agua.”*  

**¡Navega con datos, escribe con alma!** 
