// Cambiar a 'true' únicamente al hacer pruebas locales
const DEBUG = false;

// Registro central en memoria para almacenar los catálogos organizados por 'name'
const catalogosPorNombre = {};

// Variables globales para conservar las listas base sin filtrar
let rawRegimenes = [];
let rawSubRegimenes = [];

document.addEventListener("DOMContentLoaded", async () => {
    const API_URL = "/api/v1/catalogos";

    const mapeoCatalogos = {
        "ingreso": { tabla: "aduana", codigo: "aduana", texto: "descripcion" },
        "despacho": { tabla: "aduana", codigo: "aduana", texto: "descripcion" },
        "patron": { tabla: "modelo", codigo: "modelo", texto: "descripcion" },
        "a_la_frontera": { tabla: "modo_transporte", codigo: "modo_transporte", texto: "descripcion" },
        "interno": { tabla: "modo_transporte", codigo: "modo_transporte", texto: "descripcion" },
        "lugar_de_descargue": { tabla: "lugar_descargue", codigo: "lugar_descargue", texto: "descripcion" },
        "localizacion_de_la_mercancia": { tabla: "localizacion_mercancia", codigo: "localizacion_mercancia", texto: "descripcion" },
        "almacen": { tabla: "almacen", codigo: "almacen", texto: "descripcion" },
        "incoterm": { tabla: "incoterm", codigo: "incoterm", texto: "descripcion" },
        "forma_de_envio": { tabla: "forma_envio", codigo: "forma_envio", texto: "descripcion" },
        "estado_del_pago": { tabla: "estado_pago", codigo: "estado_pago", texto: "descripcion" },
        "forma_de_pago": { tabla: "forma_pago", codigo: "forma_pago", texto: "descripcion" },
        "moneda_de_transaccion": { tabla: "moneda_transaccion", codigo: "moneda_transaccion", texto: "descripcion" },
        "tipo_de_intermediario": { tabla: "tipo_intermediario", codigo: "tipo_intermediario", texto: "descripcion" },
        "vinculo_condiciones": { tabla: "tipo_vinculacion", codigo: "tipo_vinculacion", texto: "descripcion" },
        "regimen_articulo": { tabla: "regimen", codigo: "regimen", texto: "descripcion" },
        "sub_regimen_articulo": { tabla: "sub_regimen", codigo: "sub_regimen", texto: "descripcion" },
        "preferencia_articulo": { tabla: "acuerdo", codigo: "acuerdo", texto: "descripcion" },
        "rgo-a_articulo": { tabla: "criterio_origen", codigo: "criterio", texto: "descripcion" },
        "rgo-b_articulo": { tabla: "otras_instancias", codigo: "otras_instancias", texto: "descripcion" },
        "estado_articulo": { tabla: "estado_mercancia", codigo: "estado_mercancia", texto: "descripcion" },
        "embalaje_articulo": { tabla: "embalaje", codigo: "embalaje", texto: "descripcion" },
        "unidad_de_medida_articulo": { tabla: "unidad_medida", codigo: "unidad_medida", texto: "descripcion" },
        "codigo": { tabla: "documento", codigo: "documento", texto: "descripcion_documentos" }
    };

    const selectsPais = [
        "pais_del_transportista", "pais_del_medio", "pais_de_entrega",
        "pais_de_embarque", "pais_de_exportacion", "pais_de_origen",
        "pais_de_destino", "pais_intermediario", "pais_de_origen_articulo",
        "pais_articulo", "pais_documentos"
    ];

    try {
        const res = await fetch(API_URL);
        if (!res.ok) throw new Error(`Error de red: ${res.status}`);
        const datosDB = await res.json();

        // Guardar copias crudas para los filtros en cascada
        rawRegimenes = datosDB["regimen"] || [];
        rawSubRegimenes = datosDB["sub_regimen"] || [];

        // 1. Catálogos generales
        Object.entries(mapeoCatalogos).forEach(([nameAttr, config]) => {
            const registros = datosDB[config.tabla] || [];
            catalogosPorNombre[nameAttr] = registros.map(item => {
                if (config.tabla === "modelo") {
                    const codigoCombinado = `${item.modelo || ''}${item.regimen || ''}`;
                    return `${codigoCombinado} - ${item.descripcion || ''}`;
                }
                const cod = item[config.codigo] || "";
                const txt = item[config.texto] || cod;
                return `${cod} - ${txt}`;
            });
        });

        // 2. Catálogo de países
        const registrosPais = datosDB["pais"] || [];
        const listaPaises = registrosPais.map(item => {
            const cod = item.pais || item.codigo || "";
            const txt = item.descripcion || cod;
            return `${cod} - ${txt}`;
        });

        selectsPais.forEach(nameAttr => {
            catalogosPorNombre[nameAttr] = listaPaises;
        });

        // Inicializar listeners del filtrado en cascada
        aplicarFiltradoCascada();

        if (DEBUG) {
            console.log("🟢 Catálogos cargados exitosamente para:", Object.keys(catalogosPorNombre));
        }

    } catch (error) {
        if (DEBUG) {
            console.error("🔴 Error al cargar catálogos desde la API:", error);
        }
    }
});

function obtenerOpcionesInput(input) {
    if (!input || input.tagName !== "INPUT") return null;

    if (input._opcionesOriginales && input._opcionesOriginales.length > 0) {
        return input._opcionesOriginales;
    }

    const nameAttr = input.name;
    if (nameAttr && catalogosPorNombre[nameAttr]) {
        input._opcionesOriginales = catalogosPorNombre[nameAttr];
        input.removeAttribute("list");
        return input._opcionesOriginales;
    }

    return null;
}

let activeDropdown = null;
let activeInput = null;
let selectedIndex = -1;
let esModoBusquedaActual = false;

function cerrarDesplegable() {
    if (activeDropdown) {
        activeDropdown.remove();
        activeDropdown = null;
        activeInput = null;
        selectedIndex = -1;
        esModoBusquedaActual = false;
    }
}

function mostrarDesplegable(input, opciones, esBusqueda = false) {
    if (!opciones || opciones.length === 0) return;
    if (activeDropdown && activeInput === input && !esBusqueda && !esModoBusquedaActual) return;

    cerrarDesplegable();

    activeInput = input;
    esModoBusquedaActual = esBusqueda;
    const opcionesAMostrar = esBusqueda ? opciones : ["", ...opciones];

    const rect = input.getBoundingClientRect();
    const dropdown = document.createElement("div");
    dropdown.className = "pas-autocomplete-dropdown";

    dropdown.addEventListener("mousedown", (e) => {
        e.preventDefault();
    });

    Object.assign(dropdown.style, {
        position: "fixed",
        top: `${rect.bottom}px`,
        left: `${rect.left}px`,
        width: `${Math.max(rect.width, 180)}px`,
        maxHeight: "220px",
        overflowY: "auto",
        backgroundColor: "#212529",
        border: "1px solid #495057",
        borderRadius: "8px",
        boxShadow: "0 8px 16px rgba(0,0,0,0.35)",
        zIndex: "999999",
        color: "#ffffff",
        fontSize: "13px"
    });

    opcionesAMostrar.slice(0, 30).forEach((itemText, index) => {
        const item = document.createElement("div");
        item.innerHTML = itemText === "" ? "&nbsp;" : itemText;

        Object.assign(item.style, {
            padding: "6px 10px",
            cursor: "pointer",
            borderBottom: "1px solid #32383e",
            minHeight: "30px",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis"
        });

        item.addEventListener("mouseenter", () => {
            actualizarSeleccionVisual(dropdown, index);
        });

        item.addEventListener("mousedown", (e) => {
            e.preventDefault();
            input.value = itemText;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            cerrarDesplegable();
        });

        dropdown.appendChild(item);
    });

    document.body.appendChild(dropdown);
    activeDropdown = dropdown;
    selectedIndex = 0;
    actualizarSeleccionVisual(dropdown, 0);
}

function actualizarSeleccionVisual(dropdown, index) {
    const items = dropdown.children;
    for (let i = 0; i < items.length; i++) {
        if (i === index) {
            items[i].style.backgroundColor = "#0d6efd";
            items[i].style.color = "#ffffff";
        } else {
            items[i].style.backgroundColor = "transparent";
            items[i].style.color = "#ffffff";
        }
    }
    selectedIndex = index;
}

function intentarAbrirCatalogo(input) {
    if (!input || input.tagName !== "INPUT") return;
    const opciones = obtenerOpcionesInput(input);
    if (opciones && opciones.length > 0) {
        if (DEBUG) console.log(`💡 Abriendo catálogo para '${input.name}' (${opciones.length} opciones)`);
        const rawValue = input.value.trim().toLowerCase();
        if (!rawValue) {
            mostrarDesplegable(input, opciones, false);
        } else {
            mostrarDesplegable(input, opciones, true);
        }
    } else if (input.name && DEBUG) {
        console.warn(`⚠️ No se encontraron opciones de catálogo para el campo '${input.name}'`);
    }
}

document.addEventListener("focusin", (e) => {
    intentarAbrirCatalogo(e.target);
}, true);

document.addEventListener("click", (e) => {
    const input = e.target;
    if (input && input.tagName === "INPUT") {
        intentarAbrirCatalogo(input);
    } else if (activeDropdown && !activeDropdown.contains(e.target)) {
        cerrarDesplegable();
    }
}, true);

document.addEventListener("input", (e) => {
    if (!e.isTrusted || e.target !== document.activeElement) return;

    const input = e.target;
    const opciones = obtenerOpcionesInput(input);
    if (!opciones) return;

    const rawValue = input.value.trim().toLowerCase();
    if (!rawValue) {
        mostrarDesplegable(input, opciones, false);
        return;
    }

    let filtradas = [];
    if (rawValue.includes("*")) {
        const terminoLimpio = rawValue.replace(/\*/g, "").trim();
        filtradas = !terminoLimpio
            ? opciones
            : opciones.filter(val => val.toLowerCase().includes(terminoLimpio));
    } else {
        filtradas = opciones.filter(val => val.toLowerCase().startsWith(rawValue));
    }

    mostrarDesplegable(input, filtradas, true);
}, true);

document.addEventListener("scroll", (e) => {
    if (activeDropdown && (e.target === activeDropdown || activeDropdown.contains(e.target))) {
        return;
    }
    cerrarDesplegable();
}, true);

document.addEventListener("focusout", () => {
    setTimeout(() => {
        const activo = document.activeElement;
        if (activeDropdown && activo !== activeInput && !activeDropdown.contains(activo)) {
            cerrarDesplegable();
        }
    }, 150);
}, true);

document.addEventListener("keydown", (e) => {
    const input = e.target;
    const opciones = obtenerOpcionesInput(input);
    if (!opciones || !activeDropdown) return;

    const items = activeDropdown.children;

    if (e.key === "ArrowDown") {
        e.preventDefault();
        if (selectedIndex < items.length - 1) {
            actualizarSeleccionVisual(activeDropdown, selectedIndex + 1);
            items[selectedIndex].scrollIntoView({ block: "nearest" });
        }
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (selectedIndex > 0) {
            actualizarSeleccionVisual(activeDropdown, selectedIndex - 1);
            items[selectedIndex].scrollIntoView({ block: "nearest" });
        }
    } else if (e.key === "Tab" || e.key === "Enter") {
        if (selectedIndex >= 0 && items[selectedIndex]) {
            const textoSeleccionado = items[selectedIndex].textContent.trim();
            input.value = textoSeleccionado;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            cerrarDesplegable();
        }
    } else if (e.key === "Escape") {
        cerrarDesplegable();
    }
}, true);

// FUNCIÓN DE FILTRADO EN CASCADA (INDIVIDUAL POR FILA)
function aplicarFiltradoCascada() {
    document.addEventListener("change", (e) => {
        const input = e.target;

        // A. CUANDO CAMBIA EL PATRÓN (MODELO) -> Afecta a nivel general
        if (input.name === "patron") {
            const valorSeleccionado = input.value.trim(); // Ej: "ANC4 - Declaración..."
            if (!valorSeleccionado) return;

            const codigoModelo = valorSeleccionado.split(" - ")[0];
            const match = codigoModelo.match(/\d+$/);
            if (!match) return;

            const digitoRegimen = match[0]; // "4"

            // 1. Filtrar Regímenes generales que inicien con ese dígito
            const regimenesFiltrados = rawRegimenes.filter(r => 
                String(r.regimen).startsWith(digitoRegimen)
            ).map(r => `${r.regimen} - ${r.descripcion || r.regimen}`);

            // 2. Filtrar Sub-Regímenes base que inicien con ese dígito
            const subRegimenesFiltrados = rawSubRegimenes.filter(sr => 
                String(sr.regimen).startsWith(digitoRegimen)
            ).map(sr => `${sr.sub_regimen} - ${sr.descripcion || sr.sub_regimen}`);

            // 3. Actualizar catálogo base global
            catalogosPorNombre["regimen_articulo"] = regimenesFiltrados;
            catalogosPorNombre["sub_regimen_articulo"] = subRegimenesFiltrados;

            // 4. Limpiar todos los inputs y resetear sus cachés individuales
            document.querySelectorAll('input[name="regimen_articulo"], input[name="sub_regimen_articulo"]').forEach(el => {
                el.value = "";
                delete el._opcionesOriginales;
            });
        }

        // B. CUANDO CAMBIA EL RÉGIMEN EN UN ARTÍCULO -> Afecta SOLO a la casilla contigua
        if (input.name === "regimen_articulo") {
            const valorRegimen = input.value.trim();
            // Extrae los 4 dígitos exactos del código de régimen (Ej: "4000" de "4000 - Exportacion...")
            const codigoRegimen = valorRegimen.split(" - ")[0]; 

            // 1. Localizar el contenedor de la fila actual (.row, tr, o div contenedor de la sección)
            let contenedorFila = input.closest('.row, tr, .custom-card, .articulo-item, div');
            let targetSubRegimen = contenedorFila ? contenedorFila.querySelector('input[name="sub_regimen_articulo"]') : null;

            // 2. Si no hay contenedor explicito, buscar el input contigo por índice relativo en el DOM
            if (!targetSubRegimen) {
                const listaRegimenes = Array.from(document.querySelectorAll('input[name="regimen_articulo"]'));
                const listaSubRegimenes = Array.from(document.querySelectorAll('input[name="sub_regimen_articulo"]'));
                const index = listaRegimenes.indexOf(input);
                if (index !== -1 && listaSubRegimenes[index]) {
                    targetSubRegimen = listaSubRegimenes[index];
                }
            }

            // 3. Aplicar el filtro de 4 dígitos ÚNICAMENTE a ese elemento específico
            if (targetSubRegimen) {
                if (codigoRegimen && codigoRegimen.length >= 4) {
                    const subRegExactos = rawSubRegimenes.filter(sr => 
                        String(sr.regimen) === codigoRegimen
                    ).map(sr => `${sr.sub_regimen} - ${sr.descripcion || sr.sub_regimen}`);

                    // Se guarda en la propiedad interna de ESTE input especifico sin alterar las demás filas
                    targetSubRegimen._opcionesOriginales = subRegExactos;
                } else {
                    // Si se borra el régimen, hereda las opciones generales del patrón
                    delete targetSubRegimen._opcionesOriginales;
                }

                // Limpiar la casilla contigua al cambiar el régimen
                targetSubRegimen.value = "";
            }
        }
    });
}