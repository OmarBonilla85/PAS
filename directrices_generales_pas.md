# DIRECTRICES_GENERALES_PAS.md

## 1. Propósito y Alcance del Proyecto

El sistema **PAS (Programa Aduanero Sistematizado)** es una plataforma web para la gestión, aforo, clasificación arancelaria y liquidación de declaraciones aduaneras (DUCA / DVA).

Toda IA que colabore en este proyecto debe operar bajo el principio de **compatibilidad absoluta 1:1 con la lógica de negocio de SIDUNEA World** (sistema oficial de la Dirección General de Aduanas), utilizando como fuente de verdad las librerías compiladas en Java (`asytax.jar`, `asytar.jar`, `asyref.jar`, `modDAV.jar`).

---

## 2. Nomenclatura Estándar y Modelo de Datos (Estándar SIDUNEA)

Cualquier variable, modelo Pydantic, esquema SQL o propiedad de objeto JSON generado debe respetar la nomenclatura estandarizada de 3 letras de SIDUNEA:

### 2.1. Atributos de Encabezado e Ítems

| Clave Oficial | Concepto Aduanero | Campo DOM / Base de Datos |
| --- | --- | --- |
| **`TAR` / `HSC**` | Partida Arancelaria SAC (12 dígitos) | `partida_articulo` |
| **`FOB`** | Valor Comercial FOB | `total_articulo` / `fob` |
| **`FLT`** | Flete prorrateado | `flete` |
| **`INS`** | Seguro prorrateado | `seguro` |
| **`CIF`** | Valor Aduanero ($FOB + FLT + INS$) | `cif` |
| **`GRS`** | Peso Bruto (Kgs) | `peso_bruto_articulo` |
| **`NET`** | Peso Neto (Kgs) | `peso_neto_articulo` |
| **`QTY`** | Cantidad comercial / estadística | `cantidad_articulo` |
| **`UOM`** | Unidad de Medida Estadística | `unidad_de_medida_articulo` |
| **`REG`** | Régimen Aduanero (ej. `4000`) | `regimen_articulo` |
| **`SHD`** | Sub-régimen (ej. `00`) | `sub_regimen_articulo` |
| **`PRF`** | Preferencia Arancelaria (ej. `FAUCA`) | `preferencia_articulo` |
| **`CTY`** | País de Origen (ej. `CR`, `NI`) | `pais_articulo` |
| **`CP3`** | Regla Adicional RGO-A | `rgo-a_articulo` |
| **`CP4`** | Regla Adicional RGO-B | `rgo-b_articulo` |

### 2.2. Matriz de Liquidación Tributaria (`DS_Tax`)

Toda estructura de impuestos por artículo debe formatearse como una lista de objetos `TAX` con exactamente 6 propiedades:

* **`COD`**: Código del tributo (`101` DAI, `102` ISC, `103` IVA).
* **`BSE`**: Base Imponible.
* **`RAT`**: Alícuota / Tasa del impuesto (%).
* **`AMT`**: Monto calculado del tributo.
* **`MOP`**: Modo de Pago (`1` Efectivo, `2` Exonerado, `3` Fianza).
* **`TYP`**: Tipo de Tasa (`ADV` Ad-valorem, `SPE` Específico).

---

## 3. Reglas Matemáticas y Motor de Cálculo

1. **Precisión Numérica Bancaria**:
No usar redondeos estándar flotantes (`Math.round`). Todo cálculo de valores, prorrateos e impuestos debe pasar por la función `round6(num)` (precisión a 6 decimales):
```javascript
function round6(num) {
    return Math.round((Number(num) + Number.EPSILON) * 1000000) / 1000000;
}

```


2. **Prorrateo de Gastos Logísticos (Flete y Seguro)**:
* La distribución de flete y seguro entre los ítems se realiza de forma **estrictamente proporcional al valor FOB**.
* El residuo derivado del redondeo a 6 decimales se debe asignar al **último ítem** para garantizar que la suma total de las líneas coincida exactamente con los totales globales del conocimiento de embarque / factura.


3. **Cascanueces Tributario (Bases Acumuladas)**:
* **Base DAI**: $CIF = FOB + FLT + INS$
* **Base ISC**: $CIF + DAI$
* **Base IVA**: $CIF + DAI + ISC$



---

## 4. Estándares de Arquitectura de Código

### 4.1. Frontend (JS / HTML5 / Bootstrap 5)

* **Cero Frameworks Pesados**: Mantener JavaScript Vanilla para lograr máxima velocidad de carga y mínimo consumo de memoria RAM.
* **Operatividad por Teclado**: Todo control o tabla nueva debe soportar navegación mediante `Enter` (desplazamiento vertical en la misma columna) y `Ctrl + Flechas`.
* **Manipulación Dinámica del DOM**:
* Utilizar `extraerDatosDelDOM()` como único punto de entrada de recolección de datos antes de calcular o enviar al backend.
* Respetar los atributos de mapeo (`name="codigo_articulo"`, `name="partida_articulo"`, etc.) en la clonación de filas.



### 4.2. Backend (Python / FastAPI / ORM)

* Las rutas de catálogos deben mapear las tablas oficiales de `C_Tax`:
* `/api/v1/catalogos/aduanas` (`CUO_TAB`)
* `/api/v1/catalogos/incoterms` (`TOD_TAB`)
* `/api/v1/catalogos/regimenes` (`REG_TAB` / `SHD_TAB`)
* `/api/v1/catalogos/unidades` (`UOM_TAB`)


* Toda respuesta de importación Excel debe parsear campos vacíos a valores predeterminados seguros (`sub_regimen` $\rightarrow$ `"00"`, `bultos` $\rightarrow$ `0`).

---

## 5. Control de Calidad y Validaciones de Negocio

Antes de permitir la preliquidación o transmisión, la IA debe implementar o exigir los siguientes filtros de consistencia:

1. **Control de Pesos**: $Peso Net\ \le\ Peso\ Bruto$. Alerta inmediata si el peso neto supera al bruto.
2. **Partida SAC**: Verificación de longitud estricta a 12 dígitos (ej. `160100900000`).
3. **Casilla Ampliada**: Extracción y validación de expresiones regulares para fechas de vencimiento de Registros Sanitarios (`FECHA DE VENCIMIENTO: DD/MM/YYYY`).
4. **Origen vs. Preferencia**: Validar que acuerdos regionales como `FAUCA` requieran países de origen miembros del subsistema centroamericano (`CR`, `NI`, `GT`, `HN`, `SV`).

---

## 6. Regla de Oro para la IA

> **"Si una regla o cálculo no está confirmado por los archivos `.jar` de SIDUNEA World o la normativa del Sistema Arancelario Centroamericano (SAC), NO se debe asumir. Se debe descompilar o consultar la fuente oficial primero."**

---
