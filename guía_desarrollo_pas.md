# GUIA_DESARROLLO_PAS.md

## FASE 1: Consolidación del Backend y Servidor de Catálogos
> **Objetivo**: Levantar la API en Python (FastAPI) que servirá los catálogos oficiales de SIDUNEA y gestionará la persistencia de datos.

- [ ] **Paso 1.1: Configuración del Entorno Python**
  - Crear el archivo `requirements.txt` con las dependencias clave: `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `pandas`, `openpyxl`.
  - Crear la estructura de carpetas backend:
    ```text
    backend/
    ├── app/
    │   ├── main.py
    │   ├── database.py
    │   ├── models/
    │   ├── routers/
    │   └── services/
    ```

- [ ] **Paso 1.2: Base de Datos de Catálogos (`catalogo.db`)**
  - Crear la base de datos SQLite y definir los esquemas SQLAlchemy para:
    - `aduanas` (`CUO_TAB`)
    - `regimenes` (`REG_TAB` / `SHD_TAB`)
    - `incoterms` (`TOD_TAB`)
    - `unidades_medida` (`UOM_TAB`)
    - `arancel_sac` (`TAR_TAB`) -> Partidas de 12 dígitos y tasas base (DAI, ISC, IVA).

- [ ] **Paso 1.3: Endpoint Central de Catálogos**
  - Implementar la ruta GET `/api/v1/catalogos/{nombre_tabla}` en `backend/app/routers/catalogos.py`.
  - Probar la respuesta JSON desde el frontend conectando `catalogo.js`.

---

## FASE 2: Integración del Motor de Cálculo y Reglas SIDUNEA (`aforo.js`)
> **Objetivo**: Conectar el desglose de tributos de SIDUNEA World a la función de preliquidación en el navegador.

- [ ] **Paso 2.1: Implementación del Objeto `TAX` (`DS_Tax`)**
  - Actualizar la función `generarPreliquidacionAgrupada()` en `aforo.js` para que cada grupo arancelario genere su matriz de impuestos con el formato estándar:
    - `COD: 101` (DAI) | Base = CIF | Monto = Base * (DAI% / 100)
    - `COD: 102` (ISC) | Base = CIF + DAI | Monto = Base * (ISC% / 100)
    - `COD: 103` (IVA) | Base = CIF + DAI + ISC | Monto = Base * (IVA% / 100)

- [ ] **Paso 2.2: Ajuste del Prorrateo con Residuo Bancario**
  - Asegurar que la distribución del Flete (`FLT`) y Seguro (`INS`) se calcule proporcional al valor `FOB` de cada línea.
  - Implementar la asignación del residuo decimal al último ítem del grupo para evitar diferencias por redondeo en la liquidación global.

- [ ] **Paso 2.3: Renderizado de la Tabla de Preliquidación**
  - Completar el renderizado en el DOM del resumen de liquidación agrupada, mostrando subtotales por posición arancelaria y el consolidado tributario a pagar.

---

## FASE 3: Módulo de Importación Masiva desde Excel
> **Objetivo**: Cargar hojas de detalle arancelario (como `DETALLE.xls`) inyectando automáticamente las líneas de artículos al formulario.

- [ ] **Paso 3.1: Endpoint Parser de Excel**
  - Crear la ruta POST `/api/v1/importar-excel` en Python utilizando Pandas.
  - Mapear las columnas de la hoja Excel hacia el modelo estándar de datos de PAS (`partida`, `descripcion`, `fob`, `peso_bruto`, `peso_neto`, `cantidad`, `pais_origen`, `regimen`, `sub_regimen`).

- [ ] **Paso 3.2: Zona Drag & Drop en Frontend**
  - Agregar un componente visual de arrastrar y soltar archivo `.xls` / `.xlsx` dentro de la sección de Artículos en `aforo.html`.
  - Escribir la función JS que envía el archivo mediante `FormData` al backend y procesa la respuesta inyectando las filas generadas a la tabla de artículos en el DOM.

---

## FASE 4: Motor de Validaciones y Control de Calidad Pre-Declaración
> **Objetivo**: Prevenir errores antes de oficializar el pedimento mediante alertas automáticas.

- [ ] **Paso 4.1: Alertas de Control Operativo en Tiempo Real**
  - **Inconsistencia de Pesos**: Alerta visual inmediata si `Peso Neto > Peso Bruto`.
  - **Validez de Partida SAC**: Verificar que el código tenga exactamente 12 dígitos numéricos.
  - **Coherencia FAUCA**: Alerta si el régimen o acuerdo selecciona Preferencia Centroamericana pero el país de origen está fuera de la región.

- [ ] **Paso 4.2: Parser de Registros Sanitarios en Casilla Ampliada**
  - Implementar una expresión regular en JS para extraer y evaluar la fecha de vencimiento ingresada en el campo de descripción ampliada del artículo (`FECHA VENCIMIENTO: DD/MM/YYYY`).

---

## FASE 5: Exportación e Intercambio de Datos (DUCA / DVA)
> **Objetivo**: Generar la salida final de la declaración en formatos estándar de la DGA e impresión de resumen.

- [ ] **Paso 5.1: Exportador JSON / XML Estándar**
  - Crear la función que transforma el objeto retornado por `extraerDatosDelDOM()` en un archivo XML compatible con el esquema de importación de SIDUNEA.

- [ ] **Paso 5.2: Vista de Impresión del Resumen de Aforo**
  - Diseñar la hoja de estilos CSS `@media print` para imprimir una ficha limpia del resumen de aforo, valores CIF agrupados e impuestos a liquidar.
