/* Dashboard PAS — lógica de frontend (Sprint 7).
 *
 * JavaScript vanilla + Tailwind CSS (vía CDN). Consume la API REST del propio
 * backend (`/api/v1/...`) servida por FastAPI. Tres módulos:
 *   1. Buscador Arancelario (SAC): autocompletado + desglose de alícuotas.
 *   2. Calculadora Tributaria: cascada impositiva vía /liquidacion/calcular.
 *   3. Gestión de Declaraciones (DUCA): alta + historial.
 */

"use strict";

/* ------------------------------------------------------------------ */
/* Utilidades generales                                                */
/* ------------------------------------------------------------------ */

const $ = (sel) => document.querySelector(sel);

function escaparHTML(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const formatoMoneda = new Intl.NumberFormat("es-NI", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function moneda(valor) {
  const n = Number(valor);
  return Number.isFinite(n) ? formatoMoneda.format(n) : "—";
}

function porcentaje(valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  const n = Number(valor);
  return Number.isFinite(n) ? `${formatoMoneda.format(n)}%` : "—";
}

function monedaNio(valor) {
  const n = Number(valor);
  return Number.isFinite(n) ? `C$ ${formatoMoneda.format(n)}` : "—";
}

function monedaUsd(valor) {
  const n = Number(valor);
  return Number.isFinite(n) ? `$${formatoMoneda.format(n)} USD` : "—";
}

let toastTimer = null;
function toast(mensaje, ok = true) {
  const caja = $("#toast");
  const contenido = $("#toast-content");
  contenido.textContent = mensaje;
  contenido.className =
    "rounded-xl px-5 py-3 text-sm font-medium text-white shadow-lg " +
    (ok ? "bg-slate-900" : "bg-red-600");
  caja.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => caja.classList.add("hidden"), 3200);
}

async function apiFetch(url, options = {}) {
  const respuesta = await fetch(url, options);
  let datos = null;
  const tipo = respuesta.headers.get("content-type") || "";
  if (tipo.includes("application/json")) {
    datos = await respuesta.json();
  }
  if (!respuesta.ok) {
    const detalle =
      (datos && (datos.detail || datos.message)) ||
      `Error ${respuesta.status} en ${url}`;
    throw new Error(typeof detalle === "string" ? detalle : JSON.stringify(detalle));
  }
  return datos;
}

/* ------------------------------------------------------------------ */
/* Navegación entre módulos                                            */
/* ------------------------------------------------------------------ */

function showModule(nombre) {
  document.querySelectorAll(".module-panel").forEach((panel) => {
    panel.classList.add("hidden");
  });
  document.querySelectorAll(".module-tab").forEach((tab) => {
    tab.classList.remove("module-tab-active");
  });
  const panel = document.getElementById(`module-${nombre}`);
  if (panel) panel.classList.remove("hidden");
  const tab = document.querySelector(`.module-tab[data-module="${nombre}"]`);
  if (tab) tab.classList.add("module-tab-active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/* ------------------------------------------------------------------ */
/* Autocompletado de partidas (reutilizable)                           */
/* ------------------------------------------------------------------ */

function debounce(fn, espera = 250) {
  let temporizador = null;
  return function (...args) {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => fn.apply(this, args), espera);
  };
}

/**
 * Conecta un input de partida con el endpoint de búsqueda y muestra un
 * desplegable de sugerencias. Al seleccionar una opción llama ``onSelect``.
 */
function conectarAutocompletado(input, listado, onSelect) {
  let sugerencias = [];
  let indice = -1;

  function limpiar() {
    sugerencias = [];
    indice = -1;
    listado.innerHTML = "";
    listado.classList.add("hidden");
  }

  function pintar() {
    if (!sugerencias.length) {
      limpiar();
      return;
    }
    listado.innerHTML = "";
    sugerencias.forEach((item, i) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "autocomplete-item" + (i === indice ? " bg-blue-50" : "");
      boton.innerHTML =
        `<span class="autocomplete-codigo">${escaparHTML(item.partida_arancelaria)}</span>` +
        `<span class="autocomplete-desc">${escaparHTML(item.descripcion || "")}</span>`;
      boton.addEventListener("mousedown", (e) => {
        e.preventDefault();
        seleccionar(i);
      });
      listado.appendChild(boton);
    });
    listado.classList.remove("hidden");
  }

  function seleccionar(i) {
    const item = sugerencias[i];
    if (!item) return;
    input.value = item.partida_arancelaria;
    limpiar();
    if (onSelect) onSelect(item);
  }

  const buscar = debounce(async () => {
    const q = input.value.trim();
    if (q.length < 1) {
      limpiar();
      return;
    }
    try {
      const datos = await apiFetch(
        `/api/v1/arancel/buscar?q=${encodeURIComponent(q)}&limit=10`
      );
      sugerencias = datos || [];
      indice = -1;
      pintar();
    } catch (err) {
      limpiar();
    }
  }, 200);

  input.addEventListener("input", buscar);
  input.addEventListener("keydown", (e) => {
    if (listado.classList.contains("hidden")) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      indice = Math.min(indice + 1, sugerencias.length - 1);
      pintar();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      indice = Math.max(indice - 1, 0);
      pintar();
    } else if (e.key === "Enter") {
      e.preventDefault();
      seleccionar(indice >= 0 ? indice : 0);
    } else if (e.key === "Escape") {
      limpiar();
    }
  });
  input.addEventListener("blur", () => {
    setTimeout(limpiar, 120);
  });

  return { limpiar };
}

/* ------------------------------------------------------------------ */
/* MÓDULO 1: Buscador Arancelario (SAC)                                */
/* ------------------------------------------------------------------ */

function inicializarSAC() {
  const input = $("#sac-busqueda");
  const listado = $("#sac-autocomplete");
  conectarAutocompletado(input, listado, () => seleccionarPartida(input.value));
}

async function seleccionarPartida(codigo) {
  const c = (codigo || "").trim();
  if (!c) return;
  try {
    const [partida, tratados] = await Promise.all([
      apiFetch(`/api/v1/arancel/partida/${encodeURIComponent(c)}`),
      apiFetch(`/api/v1/arancel/tratados/${encodeURIComponent(c)}`).catch(() => null),
    ]);

    $("#sac-codigo").textContent = partida.partida_arancelaria;
    $("#sac-descripcion").textContent = partida.descripcion || "Sin descripción";
    $("#sac-dai").textContent = porcentaje(partida.dai);
    $("#sac-isc").textContent = porcentaje(partida.isc);
    $("#sac-iva").textContent = porcentaje(partida.iva);
    $("#sac-rir").textContent = porcentaje(partida.rir);
    $("#sac-unidad").textContent = partida.unidad
      ? `Unidad de medida: ${partida.unidad}`
      : "";

    const contenedor = $("#sac-tratados");
    contenedor.innerHTML = "";
    if (tratados && Array.isArray(tratados.tratados) && tratados.tratados.length) {
      tratados.tratados.forEach((t) => {
        const fila = document.createElement("div");
        fila.className =
          "flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2";
        fila.innerHTML =
          `<span class="text-sm text-slate-700">${escaparHTML(t.tratado)}</span>` +
          `<span class="font-mono text-sm font-semibold text-slate-900">${porcentaje(t.alicuota)}</span>`;
        contenedor.appendChild(fila);
      });
    } else {
      contenedor.innerHTML =
        '<p class="text-sm text-slate-400">No hay alícuotas preferenciales registradas para esta partida.</p>';
    }

    $("#sac-resultado").classList.remove("hidden");
    toast(`Partida ${partida.partida_arancelaria} cargada`);
  } catch (err) {
    toast(err.message, false);
  }
}

/* ------------------------------------------------------------------ */
/* MÓDULO 2: Calculadora Tributaria                                    */
/* ------------------------------------------------------------------ */

/* Acuerdos soportados por el motor de liquidación (COLUMNAS_ACUERDO). */
const ACUERDOS = [
  { codigo: "", etiqueta: "Sin acuerdo (DAI base)" },
  { codigo: "CAFTA", etiqueta: "CAFTA — TLC Centroamérica" },
  { codigo: "TLC_MEX", etiqueta: "TLC México" },
  { codigo: "TLC_RDO", etiqueta: "TLC República Dominicana" },
  { codigo: "CAFTA_RD", etiqueta: "CAFTA-RD (Rep. Dominicana)" },
  { codigo: "PANAMA", etiqueta: "TLC Panamá" },
  { codigo: "TLC_CHI", etiqueta: "TLC Chile" },
  { codigo: "UE_CA", etiqueta: "UE-Centroamérica" },
  { codigo: "DAICUBA", etiqueta: "Acuerdo parcial con Cuba" },
  { codigo: "ECUADOR", etiqueta: "Acuerdo parcial con Ecuador" },
  { codigo: "COREA", etiqueta: "TLC Corea" },
  { codigo: "TLC_GB", etiqueta: "TLC Reino Unido" },
  { codigo: "CHINA", etiqueta: "TLC Nicaragua-China" },
];

function inicializarCalculadora() {
  const select = $("#calc-acuerdo");
  select.innerHTML = "";
  ACUERDOS.forEach((a) => {
    const opcion = document.createElement("option");
    opcion.value = a.codigo;
    opcion.textContent = a.etiqueta;
    select.appendChild(opcion);
  });

  conectarAutocompletado($("#calc-partida"), $("#calc-autocomplete"));

  $("#calculadora-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const partida = $("#calc-partida").value.trim();
    const tasa = Number($("#calc-tasa").value);
    const fob = Number($("#calc-fob").value || 0);
    const flete = Number($("#calc-flete").value || 0);
    const seguro = Number($("#calc-seguro").value || 0);
    const otrosGastos = Number($("#calc-otros-gastos").value || 0);
    const deducciones = Number($("#calc-deducciones").value || 0);
    const acuerdo = $("#calc-acuerdo").value;

    if (!partida) {
      toast("Ingresa una partida arancelaria", false);
      return;
    }
    if (!(tasa > 0)) {
      toast("La tasa de cambio debe ser mayor que cero", false);
      return;
    }

    const boton = $("#calculadora-form button[type='submit']");
    boton.disabled = true;
    try {
      const datos = await apiFetch("/api/v1/liquidacion/calcular", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tasa_cambio: tasa,
          items: [
            {
              partida_arancelaria: partida,
              valor_fob: fob,
              flete,
              seguro,
              otros_gastos: otrosGastos,
              deducciones,
              codigo_acuerdo: acuerdo || null,
            },
          ],
        }),
      });
      renderResultadoCalculadora(datos);
      toast("Liquidación calculada correctamente");
    } catch (err) {
      toast(err.message, false);
    } finally {
      boton.disabled = false;
    }
  });
}

function metricasItem(item) {
  return [
    { etiqueta: "CIF USD", valor: moneda(item.cif_usd) },
    { etiqueta: "CIF NIO", valor: moneda(item.cif_nio) },
    metricaDual(`DAI (${porcentaje(item.porcentaje_dai)})`, item.dai_nio, item.dai_usd),
    metricaDual(`ISC (${porcentaje(item.porcentaje_isc)})`, item.isc_nio, item.isc_usd),
    metricaDual(`IVA (${porcentaje(item.porcentaje_iva)})`, item.iva_nio, item.iva_usd),
    metricaDual(`RIR (${porcentaje(item.porcentaje_rir)})`, item.rir_nio, item.rir_usd),
    { etiqueta: "Total NIO", valor: moneda(item.total_tributos_nio) },
    { etiqueta: "Total USD", valor: moneda(item.total_tributos_usd) },
  ];
}

function metricaDual(etiqueta, valorNio, valorUsd) {
  return {
    etiqueta,
    valores: [
      { texto: monedaNio(valorNio), clase: "metric-value" },
      { texto: monedaUsd(valorUsd), clase: "metric-value metric-value-secondary" },
    ],
  };
}

function pintarMetricas(contenedor, metricas) {
  contenedor.innerHTML = "";
  metricas.forEach((m) => {
    const div = document.createElement("div");
    div.className = "metric-card";
    const valoresHTML = (m.valores || [{ texto: m.valor }])
      .map(
        (v) =>
          `<div class="${escaparHTML(v.clase || "metric-value")}">${escaparHTML(v.texto)}</div>`
      )
      .join("");
    div.innerHTML =
      `<div class="metric-label">${escaparHTML(m.etiqueta)}</div>` + valoresHTML;
    contenedor.appendChild(div);
  });
}

function renderResultadoCalculadora(datos) {
  const items = $("#calc-items");
  items.innerHTML = "";
  (datos.items || []).forEach((item) => {
    const tarjeta = document.createElement("div");
    tarjeta.className = "rounded-xl border border-slate-200 p-4";
    const acuerdo = item.acuerdo_aplicado
      ? ` · Acuerdo aplicado: <strong>${escaparHTML(item.acuerdo_aplicado)}</strong>`
      : "";
    tarjeta.innerHTML =
      `<div class="mb-3 flex flex-wrap items-baseline justify-between gap-2">` +
      `<span class="font-mono text-sm font-semibold text-blue-700">${escaparHTML(item.partida_arancelaria)}</span>` +
      `<span class="text-xs text-slate-500">${escaparHTML(item.descripcion_partida)}${acuerdo}</span>` +
      `</div>` +
      `<div class="grid grid-cols-2 gap-2 sm:grid-cols-4"></div>`;
    pintarMetricas(tarjeta.querySelector("div.grid"), metricasItem(item));
    items.appendChild(tarjeta);
  });

  pintarMetricas($("#calc-totales"), [
    { etiqueta: "CIF USD", valor: moneda(datos.total_cif_usd) },
    { etiqueta: "CIF NIO", valor: moneda(datos.total_cif_nio) },
    metricaDual("DAI", datos.total_dai_nio, datos.total_dai_usd),
    metricaDual("ISC", datos.total_isc_nio, datos.total_isc_usd),
    metricaDual("IVA", datos.total_iva_nio, datos.total_iva_usd),
    metricaDual("RIR", datos.total_rir_nio, datos.total_rir_usd),
    { etiqueta: "Tributos NIO", valor: moneda(datos.total_tributos_nio) },
    { etiqueta: "Tributos USD", valor: moneda(datos.total_tributos_usd) },
  ]);

  $("#calc-resultado").classList.remove("hidden");
}

/* ------------------------------------------------------------------ */
/* MÓDULO 3: Gestión de Declaraciones (DUCA)                           */
/* ------------------------------------------------------------------ */

let catalogoAduanas = [];
let catalogoRegimenes = [];
let catalogoUnidades = [];

function inicializarDUCA() {
  $("#duca-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    await guardarDeclaracion();
  });
  $("#duca-regimen").addEventListener("change", poblarSubregimenes);
  cargarCatalogosDUCA();
  cargarHistorial();
}

async function cargarCatalogosDUCA() {
  try {
    const [aduanas, regimenes, unidades] = await Promise.all([
      apiFetch("/api/v1/catalogos/aduana"),
      apiFetch("/api/v1/catalogos/regimenes"),
      apiFetch("/api/v1/catalogos/unidad_medida"),
    ]);
    catalogoAduanas = aduanas || [];
    catalogoRegimenes = regimenes || [];
    catalogoUnidades = unidades || [];

    poblarSelect($("#duca-aduana"), catalogoAduanas);
    poblarSelect($("#duca-regimen"), catalogoRegimenes);
    // Refresca las unidades de los ítems que ya se hubieran dibujado antes
    // de que terminara la carga asíncrona de los catálogos.
    document.querySelectorAll("#duca-items .item-unidad").forEach((select) => {
      poblarSelect(select, catalogoUnidades);
    });
    poblarSubregimenes();
  } catch (err) {
    toast("No se pudieron cargar los catálogos: " + err.message, false);
  }
}

function poblarSelect(select, datos) {
  select.innerHTML = "";
  const vacio = document.createElement("option");
  vacio.value = "";
  vacio.textContent = "Seleccionar…";
  select.appendChild(vacio);
  (datos || []).forEach((item) => {
    const codigo = item.codigo || item.aduana || item.unidad || item.unidad_medida || item.regimen || item.id || '';
    const descripcion = item.descripcion || item.nombre || '';
    const opcion = document.createElement("option");
    opcion.value = codigo;
    opcion.textContent = `${codigo}  ${descripcion}`;
    select.appendChild(opcion);
  });
}

function poblarSubregimenes() {
  const select = $("#duca-subregimen");
  const regimen = $("#duca-regimen").value;
  select.innerHTML = "";
  const vacio = document.createElement("option");
  vacio.value = "";
  vacio.textContent = "Seleccionar…";
  select.appendChild(vacio);

  const actual = catalogoRegimenes.find(
    (r) => (r.codigo || r.regimen || "") === regimen
  );
  (actual?.sub_regimenes || []).forEach((sr) => {
    const codigo = sr.codigo || sr.id || "";
    const descripcion = sr.descripcion || sr.sub_regimen || "";
    const opcion = document.createElement("option");
    opcion.value = codigo;
    opcion.textContent = `${codigo}  ${descripcion}`;
    select.appendChild(opcion);
  });
}

function crearFilaItem(numero = 1) {
  const fila = document.createElement("tr");
  fila.dataset.item = numero;
  fila.innerHTML = `
    <td class="px-3 py-2 text-slate-500">${numero}</td>
    <td class="px-3 py-2">
      <input type="text" class="item-partida w-36 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" placeholder="0101290000000" autocomplete="off" />
    </td>
    <td class="px-3 py-2">
      <input type="text" class="item-desc w-full min-w-[160px] rounded-lg border border-slate-300 px-2 py-1.5 text-sm" placeholder="Descripción comercial" />
    </td>
    <td class="px-3 py-2">
      <input type="number" class="item-cantidad w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" min="0" step="0.01" value="1" />
    </td>
    <td class="px-3 py-2">
      <select class="item-unidad w-32 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"></select>
    </td>
    <td class="px-3 py-2">
      <input type="number" class="item-fob w-28 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" min="0" step="0.01" placeholder="0.00" />
    </td>
    <td class="px-3 py-2">
      <input type="number" class="item-flete w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" min="0" step="0.01" value="0" />
    </td>
    <td class="px-3 py-2">
      <input type="number" class="item-seguro w-24 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" min="0" step="0.01" value="0" />
    </td>
    <td class="px-3 py-2">
      <input type="number" class="item-otros-gastos w-28 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" min="0" step="0.01" value="0" />
    </td>
    <td class="px-3 py-2">
      <input type="number" class="item-deducciones w-28 rounded-lg border border-slate-300 px-2 py-1.5 text-sm" min="0" step="0.01" value="0" />
    </td>
    <td class="px-3 py-2 text-right">
      <button type="button" class="eliminar-item rounded-lg px-2 py-1 text-slate-400 hover:bg-red-50 hover:text-red-600" title="Eliminar ítem">✕</button>
    </td>`;
  return fila;
}

function renumerarItems() {
  document.querySelectorAll("#duca-items tr").forEach((fila, i) => {
    fila.dataset.item = i + 1;
    fila.querySelector("td").textContent = i + 1;
  });
}

function agregarItem() {
  const cuerpo = $("#duca-items");
  const fila = crearFilaItem(cuerpo.children.length + 1);
  poblarSelect(fila.querySelector(".item-unidad"), catalogoUnidades);
  fila.querySelector(".eliminar-item").addEventListener("click", () => {
    fila.remove();
    renumerarItems();
  });
  cuerpo.appendChild(fila);
  return fila;
}

function cargarDatosEjemplo() {
  $("#duca-importador").value = "Importador de Prueba S.A.";
  $("#duca-aduana").value = "0110";
  $("#duca-regimen").value = "1000";
  poblarSubregimenes();
  $("#duca-subregimen").value = "1000000";
  $("#duca-tasa").value = "36.6243";

  $("#duca-items").innerHTML = "";
  const fila = agregarItem();
  fila.querySelector(".item-partida").value = "0101290000000";
  fila.querySelector(".item-desc").value = "Caballos vivos (excepto reproductores)";
  fila.querySelector(".item-cantidad").value = "2";
  fila.querySelector(".item-unidad").value = "05";
  fila.querySelector(".item-fob").value = "1000";
  fila.querySelector(".item-flete").value = "100";
  fila.querySelector(".item-seguro").value = "20";
  fila.querySelector(".item-otros-gastos").value = "0";
  fila.querySelector(".item-deducciones").value = "0";

  toast("Datos de ejemplo cargados");
}

async function guardarDeclaracion() {
  const importador = $("#duca-importador").value.trim();
  const aduana = $("#duca-aduana").value;
  const regimen = $("#duca-regimen").value;
  const subregimen = $("#duca-subregimen").value;
  const tasa = Number($("#duca-tasa").value);

  if (!importador || !aduana || !regimen || !subregimen) {
    toast("Completa importador, aduana, régimen y sub-régimen", false);
    return;
  }
  if (!(tasa > 0)) {
    toast("La tasa de cambio debe ser mayor que cero", false);
    return;
  }

  const items = [];
  const filas = document.querySelectorAll("#duca-items tr");
  for (const fila of filas) {
    const partida = fila.querySelector(".item-partida").value.trim();
    const descripcion = fila.querySelector(".item-desc").value.trim();
    const cantidad = Number(fila.querySelector(".item-cantidad").value || 0);
    const unidad = fila.querySelector(".item-unidad").value;
    const fob = Number(fila.querySelector(".item-fob").value || 0);
    const flete = Number(fila.querySelector(".item-flete").value || 0);
    const seguro = Number(fila.querySelector(".item-seguro").value || 0);
    const otrosGastos = Number(fila.querySelector(".item-otros-gastos").value || 0);
    const deducciones = Number(fila.querySelector(".item-deducciones").value || 0);

    if (!partida || !descripcion || !unidad) {
      toast("Cada ítem requiere partida, descripción y unidad de medida", false);
      return;
    }
    items.push({
      partida_arancelaria: partida,
      descripcion_comercial: descripcion,
      cantidad,
      unidad_medida: unidad,
      valor_fob_usd: fob,
      flete_usd: flete,
      seguro_usd: seguro,
      otros_gastos_usd: otrosGastos,
      deducciones_usd: deducciones,
    });
  }

  if (!items.length) {
    toast("Agrega al menos un ítem a la declaración", false);
    return;
  }

  const boton = $("#duca-form button[type='submit']");
  boton.disabled = true;
  try {
    const datos = await apiFetch("/api/v1/declaraciones", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        aduana_codigo: aduana,
        regimen_codigo: regimen,
        subregimen_codigo: subregimen,
        importador_nombre: importador,
        tasa_cambio: tasa,
        items,
      }),
    });
    toast(`Declaración ${datos.numero_declaracion} guardada`);
    $("#duca-form").reset();
    $("#duca-tasa").value = "36.6243";
    $("#duca-items").innerHTML = "";
    agregarItem();
    cargarHistorial();
  } catch (err) {
    toast(err.message, false);
  } finally {
    boton.disabled = false;
  }
}

async function cargarHistorial() {
  const cuerpo = $("#duca-historial");
  cuerpo.innerHTML =
    '<tr><td colspan="10" class="px-3 py-6 text-center text-sm text-slate-400">Cargando…</td></tr>';
  try {
    const datos = await apiFetch("/api/v1/declaraciones?skip=0&limit=50");
    cuerpo.innerHTML = "";
    if (!datos || !datos.length) {
      cuerpo.innerHTML =
        '<tr><td colspan="10" class="px-3 py-6 text-center text-sm text-slate-400">No hay declaraciones registradas.</td></tr>';
      return;
    }
    datos.forEach((d) => {
      const fila = document.createElement("tr");
      fila.className = "hover:bg-slate-50";
      const fecha = d.fecha_creacion
        ? new Date(d.fecha_creacion).toLocaleString("es-NI")
        : "—";
      const tributosUsd =
        Number(d.tasa_cambio) > 0
          ? Number(d.total_tributos_nio) / Number(d.tasa_cambio)
          : null;
      fila.innerHTML = `
        <td class="px-3 py-2 font-mono text-xs font-semibold text-blue-700">${escaparHTML(d.numero_declaracion)}</td>
        <td class="px-3 py-2">${escaparHTML(d.importador_nombre)}</td>
        <td class="px-3 py-2 text-slate-500">${escaparHTML(d.aduana_codigo)}</td>
        <td class="px-3 py-2 text-slate-500">${escaparHTML(d.regimen_codigo)}</td>
        <td class="px-3 py-2 text-right font-mono">${moneda(d.total_fob_usd)}</td>
        <td class="px-3 py-2 text-right font-mono">${moneda(d.total_cif_usd)}</td>
        <td class="px-3 py-2 text-right font-mono font-semibold">${monedaNio(d.total_tributos_nio)}</td>
        <td class="px-3 py-2 text-right font-mono">${monedaUsd(tributosUsd)}</td>
        <td class="px-3 py-2"><span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">${escaparHTML(d.estado)}</span></td>
        <td class="px-3 py-2 text-xs text-slate-500">${escaparHTML(fecha)}</td>`;
      cuerpo.appendChild(fila);
    });
  } catch (err) {
    cuerpo.innerHTML =
      `<tr><td colspan="10" class="px-3 py-6 text-center text-sm text-red-500">${escaparHTML(err.message)}</td></tr>`;
  }
}

/* ------------------------------------------------------------------ */
/* Estado de la API e inicialización                                   */
/* ------------------------------------------------------------------ */

async function verificarAPI() {
  const dot = $("#api-status-dot");
  const texto = $("#api-status-text");
  try {
    const datos = await apiFetch("/health");
    dot.className = "h-2 w-2 rounded-full bg-emerald-400";
    texto.textContent = datos && datos.status === "online" ? "API en línea" : "API disponible";
  } catch (err) {
    dot.className = "h-2 w-2 rounded-full bg-red-500";
    texto.textContent = "API no disponible";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  verificarAPI();
  inicializarSAC();
  inicializarCalculadora();
  inicializarDUCA();
  agregarItem();
});
