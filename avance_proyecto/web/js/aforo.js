// web/aforo.js

/**
 * Operación de redondeo con precisión bancaria a 6 decimales
 */
function round6(num) {
    return Math.round((Number(num) + Number.EPSILON) * 1000000) / 1000000;
}

/**
 * Agrupa los artículos del detalle según la clave de Posición Arancelaria
 */
function generarPreliquidacionAgrupada() {
    const { globales, items } = extraerDatosDelDOM(); // Función existente en aforo.js
    if (!items || items.length === 0) {
        renderizarTablaPosiciones([], globales);
        return;
    }

    const posicionesMap = new Map();

    // 1. Agrupar por Criterios Tributarios y Arancelarios
    items.forEach(item => {
        // Clave única de agrupación
        const claveGrupo = [
            item.partida || "0000.00.00",
            item.regimen || "4000",
            item.sub_regimen || "00",
            item.acuerdo || "GRAL",
            item.pais_origen || "GEN",
            item.codigo_adicional || "000",
            item.tratamiento_tributario || "CG",
            item.dai_pct || 0,
            item.isc_pct || 0,
            item.iva_pct || 0
        ].join("|");

        if (!posicionesMap.has(claveGrupo)) {
            posicionesMap.set(claveGrupo, {
                partida: item.partida,
                regimen: item.regimen,
                sub_regimen: item.sub_regimen,
                acuerdo: item.acuerdo,
                pais_origen: item.pais_origen,
                rgo_a: item.codigo_adicional,
                rgo_b: item.tratamiento_tributario,
                bultos: 0,
                peso_bruto: 0.0,
                peso_neto: 0.0,
                cantidad_est: 0.0,
                fob: 0.0,
                flete: 0.0,
                seguro: 0.0,
                cif: 0.0,
                elementos: []
            });
        }

        const grupo = posicionesMap.get(claveGrupo);
        grupo.bultos += parseInt(item.bultos || 0, 10);
        grupo.peso_bruto = round6(grupo.peso_bruto + (item.peso_bruto || 0));
        grupo.peso_neto = round6(grupo.peso_neto + (item.peso_neto || 0));
        grupo.cantidad_est = round6(grupo.cantidad_est + (item.cantidad || 0));
        grupo.fob = round6(grupo.fob + item.fob);
        grupo.elementos.push(item);
    });

    const posiciones = Array.from(posicionesMap.values());
    const fobTotalAcumulado = round6(posiciones.reduce((acc, p) => acc + p.fob, 0));

    // 2. Prorratear Flete y Seguro a 6 dígitos con ajuste de residuo bancario
    let fleteAsignado = 0.0;
    let seguroAsignado = 0.0;

    posiciones.forEach((pos, index) => {
        if (index === posiciones.length - 1) {
            // El último grupo absorbe el residuo para cuadrar exactamente el 100%
            pos.flete = round6(globales.flete_total - fleteAsignado);
            pos.seguro = round6(globales.seguro_total - seguroAsignado);
        } else {
            const factorFob = fobTotalAcumulado > 0 ? (pos.fob / fobTotalAcumulado) : 0;
            pos.flete = round6(globales.flete_total * factorFob);
            pos.seguro = round6(globales.seguro_total * factorFob);

            fleteAsignado = round6(fleteAsignado + pos.flete);
            seguroAsignado = round6(seguroAsignado + pos.seguro);
        }

        pos.cif = round6(pos.fob + pos.flete + pos.seguro);
    });

    renderizarTablaPosiciones(posiciones, globales);
}

/**
 * Renderiza la tabla de posiciones agrupadas en el DOM
 */
function renderizarTablaPosiciones(posiciones, globales) {
    const tbody = document.getElementById("tbody_posiciones");
    const tfoot = document.getElementById("tfoot_posiciones");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (posiciones.length === 0) {
        tbody.innerHTML = `<tr><td colspan="16" class="text-center text-muted py-3">No hay artículos registrados en el detalle.</td></tr>`;
        if (tfoot) tfoot.innerHTML = "";
        return;
    }

    let totBultos = 0, totPBruto = 0, totPNeto = 0, totCant = 0;
    let totFob = 0, totFlete = 0, totSeguro = 0, totCif = 0;

    posiciones.forEach((pos, idx) => {
        totBultos += pos.bultos;
        totPBruto = round6(totPBruto + pos.peso_bruto);
        totPNeto = round6(totPNeto + pos.peso_neto);
        totCant = round6(totCant + pos.cantidad_est);
        totFob = round6(totFob + pos.fob);
        totFlete = round6(totFlete + pos.flete);
        totSeguro = round6(totSeguro + pos.seguro);
        totCif = round6(totCif + pos.cif);

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td class="text-center fw-bold">${idx + 1}</td>
            <td class="font-monospace">${pos.partida}</td>
            <td class="text-center">${pos.regimen}</td>
            <td class="text-center">${pos.sub_regimen}</td>
            <td class="text-center">${pos.acuerdo || '-'}</td>
            <td class="text-center">${pos.pais_origen || '-'}</td>
            <td class="text-center">${pos.rgo_a || '000'}</td>
            <td class="text-center">${pos.rgo_b || 'CG'}</td>
            <td class="text-end">${pos.bultos}</td>
            <td class="text-end font-monospace">${pos.peso_bruto.toFixed(6)}</td>
            <td class="text-end font-monospace">${pos.peso_neto.toFixed(6)}</td>
            <td class="text-end font-monospace">${pos.cantidad_est.toFixed(6)}</td>
            <td class="text-end font-monospace fw-bold">${pos.fob.toFixed(6)}</td>
            <td class="text-end font-monospace">${pos.flete.toFixed(6)}</td>
            <td class="text-end font-monospace">${pos.seguro.toFixed(6)}</td>
            <td class="text-end font-monospace fw-bold text-primary">${pos.cif.toFixed(6)}</td>
        `;
        tbody.appendChild(tr);
    });

    if (tfoot) {
        tfoot.innerHTML = `
            <tr>
                <td colspan="8" class="text-start">TOTALES PRELIQUIDACIÓN:</td>
                <td>${totBultos}</td>
                <td class="font-monospace">${totPBruto.toFixed(6)}</td>
                <td class="font-monospace">${totPNeto.toFixed(6)}</td>
                <td class="font-monospace">${totCant.toFixed(6)}</td>
                <td class="font-monospace">${totFob.toFixed(6)}</td>
                <td class="font-monospace">${totFlete.toFixed(6)}</td>
                <td class="font-monospace">${totSeguro.toFixed(6)}</td>
                <td class="font-monospace text-primary">${totCif.toFixed(6)}</td>
            </tr>
        `;
    }
}