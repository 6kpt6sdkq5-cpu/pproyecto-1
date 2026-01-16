# Sistema de Gestión de Restaurante

Una aplicación web completa para la gestión de un restaurante con sistema de usuarios y roles diferenciados, incluyendo manejo de comprobantes Yape.

## Características

### Sistema de Usuarios con Roles
- **8 Meseros** (mesero1 - mesero8): Contraseña `mesero123`
- **2 Gerentes** (gerente1 - gerente2): Contraseña `gerente123`
- **1 Administrador** (admin): Contraseña `1234`

### Funcionalidades por Rol

#### Meseros
- ✅ Subir fotos de comprobantes Yape
- ✅ Ver reporte personal diario
- ✅ Ver sus propios comprobantes subidos

#### Gerentes
- ✅ Validar pagos Yape con número de operación y código de seguridad
- ✅ Ver todos los comprobantes del día
- ✅ Descargar ZIP con todos los comprobantes
- ✅ Generar reporte diario completo
- ✅ Gestión de comprobantes (validar/rechazar)

#### Administrador
- ✅ Gestión completa del menú (agregar/eliminar platos)
- ✅ Gestión de usuarios (activar/desactivar)
- ✅ Validación de pagos Yape
- ✅ Descarga de comprobantes
- ✅ Reportes completos

## Instalación

1. Clonar o descargar el proyecto
2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
python app.py
```

4. Abrir el navegador en: `http://localhost:5000`

## Uso

### Login
- Acceder a `http://localhost:5000/login`
- Usar las credenciales según el rol deseado

### Flujo de Trabajo

1. **Meseros** suben comprobantes Yape desde su panel
2. **Gerentes** validan los comprobantes con número de operación y código de seguridad
3. **Administrador** gestiona el menú y usuarios

### Estructura de Archivos
```
restaurant_app/
├── app.py              # Aplicación principal Flask
├── restaurant_db.json  # Base de datos JSON
├── comprobantes_yape/  # Carpeta de comprobantes subidos
├── static/             # Archivos estáticos (CSS, JS)
├── templates/          # Plantillas HTML
└── README.md          # Este archivo
```

## Seguridad
- Sistema de autenticación por sesiones
- Control de acceso basado en roles
- Verificación de usuarios activos/inactivos
- Validación de archivos subidos

## Notas
- La aplicación está en modo desarrollo
- Los comprobantes se almacenan localmente
- Se recomienda implementar respaldo de datos en producción
- La validación bancaria es simulada en esta versión

## Despliegue en Render

1. Subir el proyecto a GitHub
2. En Render, crear un Blueprint con este repositorio
3. Variables de entorno:
   - `SECRET_KEY`: clave de sesión
   - `FLASK_DEBUG` opcional (`1` para debug)
4. Render detecta:
   - `rootDir`: `restaurant_app`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`

## Despliegue en Vercel (serverless, sin disco persistente)

1. Importar el repositorio en Vercel
2. Vercel detecta Python con `@vercel/python` usando `vercel.json`
3. Limitaciones: no hay disco persistente; se usa `/tmp` en tiempo de ejecución
4. Variables de entorno (opcionales):
   - `SECRET_KEY`
   - `DB_FILE` (por defecto `/tmp/restaurant_db.json`)
   - `UPLOAD_FOLDER` (por defecto `/tmp/comprobantes_yape`)
5. Para persistencia real, usa Render con disco `/data`
