document.addEventListener('DOMContentLoaded', function () {
    const tableSelector = '.table';

    // --- 1. NAVEGACIÓN CON TECLADO EN TABLAS (Ctrl + Flechas) ---
    const getFocusableTableElements = (table) => {
        return Array.from(table.querySelectorAll('input, select, textarea, button, a[href], [tabindex]'))
            .filter(el => {
                if (!(el instanceof HTMLElement)) return false;
                if (el.disabled) return false;
                if (el.tabIndex === -1) return false;
                if (el.offsetParent === null) return false;
                if (el.matches('input')) {
                    return el.type !== 'hidden';
                }
                return true;
            });
    };

    const focusSameColumnRow = (current, direction) => {
        const cell = current.closest('td');
        const row = current.closest('tr');
        if (!cell || !row) return;
        const table = row.closest('table');
        if (!table) return;
        const cells = Array.from(row.children);
        const columnIndex = cells.indexOf(cell);
        const targetRow = direction === 'up' ? row.previousElementSibling : row.nextElementSibling;
        if (!targetRow) return;
        const targetCells = Array.from(targetRow.children);
        if (columnIndex < 0 || columnIndex >= targetCells.length) return;
        const targetCell = targetCells[columnIndex];
        const focusable = targetCell.querySelector('input, select, textarea, button, a[href], [tabindex]');
        if (focusable && focusable instanceof HTMLElement && !focusable.disabled && focusable.tabIndex !== -1) {
            focusable.focus();
        }
    };

    document.addEventListener('keydown', (event) => {
        const target = event.target;
        const isTextInput = target instanceof HTMLInputElement && (target.type === 'text' || target.type === 'date' || target.type === 'number');
        const isSelect = target instanceof HTMLSelectElement;
        if (!isTextInput && !isSelect) return;

        const table = target.closest(tableSelector);
        if (!table) return;

        const key = event.key;

        // --- NUEVO: NAVEGACIÓN VERTICAL CON TECLA ENTER ---
        if (key === 'Enter') {
            event.preventDefault();
            focusSameColumnRow(target, 'down');
            return;
        }

        // --- NAVEGACIÓN CON COMBINACIÓN CTRL + FLECHAS ---
        if (event.ctrlKey) {
            if (key === 'ArrowUp' || key === 'ArrowDown') {
                event.preventDefault();
                focusSameColumnRow(target, key === 'ArrowUp' ? 'up' : 'down');
            }
            if (key === 'ArrowLeft' || key === 'ArrowRight') {
                event.preventDefault();
                const focusables = getFocusableTableElements(table);
                const index = focusables.indexOf(target);
                if (index === -1) return;
                const nextIndex = key === 'ArrowLeft' ? index - 1 : index + 1;
                if (focusables[nextIndex]) {
                    focusables[nextIndex].focus();
                }
            }
        }
    });

    function generarCodigo(longitud = 10) {
        const caracteres = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let resultado = '';
        for (let i = 0; i < longitud; i++) {
            resultado += caracteres.charAt(Math.floor(Math.random() * caracteres.length));
        }
        return resultado;
    }

    // --- NUEVO: FUNCIONES AUXILIARES PARA RELACIONAR FACTURAS CON ARTÍCULOS ---
    function mostrarArticulosDeFactura(facturaId) {
        const tablaArticulos = document.getElementById('tabla_articulos');
        if (tablaArticulos) {
            tablaArticulos.querySelectorAll('tbody[factura]').forEach(tbody => {
                const attrFactura = tbody.getAttribute('factura');
                // Mantener siempre oculta la plantilla base
                if (attrFactura === 'factura') {
                    tbody.style.display = 'none';
                    return;
                }
                tbody.style.display = (attrFactura === facturaId) ? '' : 'none';
            });
        }
    }

    function clonarTbodyArticulosParaFactura(facturaId) {
        const tablaArticulos = document.getElementById('tabla_articulos');
        if (tablaArticulos) {
            const plantillaTbodyArt = tablaArticulos.querySelector('tbody[factura="factura"]');
            if (plantillaTbodyArt) {
                const nuevoTbodyArt = plantillaTbodyArt.cloneNode(true);
                nuevoTbodyArt.setAttribute('factura', facturaId);
                nuevoTbodyArt.style.display = '';

                // Cambiar el id de la primera fila de artículo si tiene ID 'articulo'
                const trArticulo = nuevoTbodyArt.querySelector('#articulo');
                if (trArticulo) {
                    trArticulo.id = `articulo_${generarCodigo(10)}`;
                }

                tablaArticulos.appendChild(nuevoTbodyArt);
                mostrarArticulosDeFactura(facturaId);
            }
        }
    }

    const navTabs = document.getElementById('nav-tabs-dva');
    const contenedorPrincipal = document.getElementById('proveedor_contenedor');
    const tablaFacturas = document.getElementById('tabla_facturas');

    // Mapeo de los elementos dinámicos que deben responder en paralelo al flujo del proveedor.
    // 'idContenedorPadre' es donde buscaremos la plantilla y añadiremos los clones.
    // 'atributoCustom' es el nombre del atributo personalizado (ej: proveedor="...", intermediario="...")
    const componentesEspejo = [
        { idContenedorPadre: 'intermediario', atributoCustom: 'intermediario' },
        { idContenedorPadre: 'condiciones', atributoCustom: 'condiciones' },
        { idContenedorPadre: 'conformacion', atributoCustom: 'conformacion' } // Nota: 'conformacion' en atributo sin tilde según tu descripción
    ];

    if (navTabs && contenedorPrincipal) {

        // --- 1. LÓGICA PARA ELIMINAR PESTAÑAS, PANELES Y COMPONENTES ESPEJO ---
        navTabs.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-delete-tab') || e.target.closest('.btn-delete-tab')) {
                e.preventDefault();

                const boton = e.target.classList.contains('btn-delete-tab') ? e.target : e.target.closest('.btn-delete-tab');
                const enlace = boton.closest('a');
                const liPadre = boton.closest('li');

                if (enlace) {
                    const hrefValue = enlace.getAttribute('href').replace('#', '');
                    const panelContenido = document.getElementById(hrefValue);
                    const estabaActiva = enlace.classList.contains('active');

                    // A. Eliminar el tbody asociado en la tabla de facturas y sus artículos relacionados
                    if (tablaFacturas) {
                        const tbodyAsociado = tablaFacturas.querySelector(`tbody[proveedor="${hrefValue}"]`);
                        if (tbodyAsociado) {
                            // Eliminar también los tbodys de artículos asociados a las facturas de este tbody
                            tbodyAsociado.querySelectorAll('tr[id^="factura_"]').forEach(tr => {
                                const tablaArticulos = document.getElementById('tabla_articulos');
                                if (tablaArticulos) {
                                    const tbodyArt = tablaArticulos.querySelector(`tbody[factura="${tr.id}"]`);
                                    if (tbodyArt) tbodyArt.remove();
                                }
                            });
                            tbodyAsociado.remove();
                        }
                    }

                    // B. Eliminar dinámicamente los elementos de Intermediario, Condiciones y Conformación
                    componentesEspejo.forEach(comp => {
                        const contenedorPadre = document.getElementById(comp.idContenedorPadre);
                        if (contenedorPadre) {
                            const elementoAsociado = contenedorPadre.querySelector(`[${comp.atributoCustom}="${hrefValue}"]`);
                            if (elementoAsociado) elementoAsociado.remove();
                        }
                    });

                    // C. Remover el formulario y la pestaña física
                    if (panelContenido) panelContenido.remove();
                    if (liPadre) liPadre.remove();

                    if (estabaActiva) {
                        const pestañasRestantes = navTabs.querySelectorAll('li:not([style*="display: none"]) .nav-link:not([href="#adicionar"])');
                        if (pestañasRestantes.length > 0) {
                            const ultimaTab = pestañasRestantes[pestañasRestantes.length - 1];
                            const bsTab = bootstrap.Tab.getOrCreateInstance(ultimaTab);
                            bsTab.show();
                        }
                    }
                }
            }
        });

        // --- 2. LÓGICA PARA AGREGAR NUEVAS PESTAÑAS Y CLONAR COMPONENTES (Botón +) ---
        const botonAgregar = navTabs.querySelector('a[href="#adicionar"]');

        if (botonAgregar) {
            botonAgregar.addEventListener('click', (e) => {
                e.preventDefault();

                // 1. Clonar la pestaña plantilla del Proveedor
                const plantillaLi = navTabs.querySelector('li:first-child');
                if (!plantillaLi) return;

                const nuevoLi = plantillaLi.cloneNode(true);
                nuevoLi.style.display = 'block';

                const codigoAleatorio = generarCodigo(10);
                const nuevoIdCompuesto = `proveedor_${codigoAleatorio}`;

                // 2. Configurar el enlace de la pestaña nueva
                const nuevoEnlace = nuevoLi.querySelector('a');
                if (nuevoEnlace) {
                    nuevoEnlace.setAttribute('href', `#${nuevoIdCompuesto}`);
                    nuevoEnlace.setAttribute('data-bs-toggle', 'pill');
                    nuevoEnlace.classList.remove('active');
                }

                // 3. Clonar el panel de contenido (Formulario de Proveedor)
                const plantillaContenido = document.getElementById('proveedor');
                if (plantillaContenido) {
                    const nuevoContenido = plantillaContenido.cloneNode(true);
                    nuevoContenido.id = nuevoIdCompuesto;
                    nuevoContenido.classList.remove('show', 'active');
                    nuevoContenido.classList.add('tab-pane', 'fade');
                    contenedorPrincipal.appendChild(nuevoContenido);
                }

                // 4. Clonar el tbody para la tabla de facturas
                if (tablaFacturas) {
                    const plantillaTbody = tablaFacturas.querySelector('tbody[proveedor="proveedor"]');
                    if (plantillaTbody) {
                        const nuevoTbody = plantillaTbody.cloneNode(true);
                        nuevoTbody.setAttribute('proveedor', nuevoIdCompuesto);
                        nuevoTbody.style.display = '';
                        const trFactura = nuevoTbody.querySelector('#factura');
                        let nuevoIdFactura = '';
                        if (trFactura) {
                            nuevoIdFactura = `factura_${generarCodigo(10)}`;
                            trFactura.id = nuevoIdFactura;
                        }
                        tablaFacturas.appendChild(nuevoTbody);
                        if (nuevoIdFactura) {
                            clonarTbodyArticulosParaFactura(nuevoIdFactura);
                        }
                    }

                    // Ocultar temporalmente los demás tboddys
                    tablaFacturas.querySelectorAll('tbody').forEach(tbody => {
                        if (tbody.getAttribute('proveedor') !== nuevoIdCompuesto) {
                            tbody.style.display = 'none';
                        }
                    });
                }

                // NUEVO: 5. Clonar e insertar dinámicamente Intermediario, Condiciones y Conformación
                componentesEspejo.forEach(comp => {
                    const contenedorPadre = document.getElementById(comp.idContenedorPadre);
                    if (contenedorPadre) {
                        // Buscamos la plantilla base que tiene el atributo igual a "proveedor"
                        const plantillaComponente = contenedorPadre.querySelector(`[${comp.atributoCustom}="proveedor"]`);
                        if (plantillaComponente) {
                            const nuevoComponente = plantillaComponente.cloneNode(true);

                            // Configuramos el nuevo ID compuesto y lo hacemos visible
                            nuevoComponente.setAttribute(comp.atributoCustom, nuevoIdCompuesto);
                            nuevoComponente.style.display = '';

                            // Insertamos el clon en su respectivo contenedor padre
                            contenedorPadre.appendChild(nuevoComponente);
                        }

                        // Ocultamos todos los elementos hermanos en este contenedor excepto el recién creado
                        contenedorPadre.querySelectorAll(`[${comp.atributoCustom}]`).forEach(el => {
                            if (el.getAttribute(comp.atributoCustom) !== nuevoIdCompuesto) {
                                el.style.display = 'none';
                            }
                        });
                    }
                });

                // 6. Insertar la pestaña física antes del botón (+)
                const liBotonAgregar = botonAgregar.closest('li');
                navTabs.insertBefore(nuevoLi, liBotonAgregar);

                // 7. Activar de manera nativa la pestaña mediante Bootstrap
                if (nuevoEnlace) {
                    const bsTab = new bootstrap.Tab(nuevoEnlace);
                    bsTab.show();
                }
            });
        }

        // --- 3. LÓGICA PARA ALTERNAR ELEMENTOS AL CAMBIAR DE PESTAÑA (shown.bs.tab) ---
        navTabs.addEventListener('shown.bs.tab', (e) => {
            const enlaceActivo = e.target;
            const idProveedor = enlaceActivo.getAttribute('href').replace('#', '');

            if (idProveedor === 'adicionar') return;

            // A. Alternar visualización en la tabla de facturas
            if (tablaFacturas) {
                tablaFacturas.querySelectorAll('tbody').forEach(tbody => {
                    const attrProveedor = tbody.getAttribute('proveedor');
                    if (attrProveedor === 'proveedor') {
                        tbody.style.display = 'none';
                        return;
                    }
                    tbody.style.display = (attrProveedor === idProveedor) ? '' : 'none';
                });

                // Mostrar los artículos de la primera factura visible en este proveedor
                const primerTbodyVisible = tablaFacturas.querySelector(`tbody[proveedor="${idProveedor}"]`);
                if (primerTbodyVisible) {
                    const primeraFilaFactura = primerTbodyVisible.querySelector('tr[id^="factura_"]');
                    if (primeraFilaFactura) {
                        mostrarArticulosDeFactura(primeraFilaFactura.id);
                    }
                }
            }

            // NUEVO: B. Alternar visualización en Intermediario, Condiciones y Conformación
            componentesEspejo.forEach(comp => {
                const contenedorPadre = document.getElementById(comp.idContenedorPadre);
                if (contenedorPadre) {
                    contenedorPadre.querySelectorAll(`[${comp.atributoCustom}]`).forEach(el => {
                        const attrValor = el.getAttribute(comp.atributoCustom);

                        // Mantener siempre oculta la plantilla base original
                        if (attrValor === 'proveedor') {
                            el.style.display = 'none';
                            return;
                        }

                        // Si coincide con el ID del proveedor activo se muestra, de lo contrario se oculta
                        el.style.display = (attrValor === idProveedor) ? '' : 'none';
                    });
                }
            });
        });
    }

    // --- 4. LÓGICA PARA AGREGAR FILAS EN LA TABLA DE FACTURAS (Botón + con name="agregar_fila") ---
    document.addEventListener('click', (e) => {
        if (e.target && e.target.matches('button[name="agregar_fila"]')) {
            e.preventDefault();
            const tbodyPadre = e.target.closest('tbody');
            if (tbodyPadre) {
                const plantillaTr = document.getElementById('factura');
                if (plantillaTr) {
                    const nuevoTr = plantillaTr.cloneNode(true);
                    const nuevoIdFactura = `factura_${generarCodigo(10)}`;
                    nuevoTr.id = nuevoIdFactura;
                    tbodyPadre.appendChild(nuevoTr);
                    clonarTbodyArticulosParaFactura(nuevoIdFactura);
                }
            }
        }
    });

    // --- 5. LÓGICA AL SELECCIONAR ELEMENTOS DE UNA FILA EN LA TABLA DE FACTURAS ---
    if (tablaFacturas) {
        const seleccionarFilaFactura = (e) => {
            const tr = e.target.closest('tr');
            if (tr && tr.id && tr.id.startsWith('factura_')) {
                mostrarArticulosDeFactura(tr.id);
            }
        };
        tablaFacturas.addEventListener('click', seleccionarFilaFactura);
        tablaFacturas.addEventListener('focusin', seleccionarFilaFactura);
    }

    // --- NUEVO: LÓGICA PARA AGREGAR FILAS EN LA TABLA DE ARTÍCULOS ---
    const tablaArticulos = document.getElementById('tabla_articulos');
    if (tablaArticulos) {
        tablaArticulos.addEventListener('click', (e) => {
            if (e.target && e.target.tagName === 'BUTTON' && e.target.textContent.trim() === '+') {
                e.preventDefault();
                const tbodyPadre = e.target.closest('tbody');
                if (tbodyPadre) {
                    const plantillaTbody = tablaArticulos.querySelector('tbody[factura="factura"]');
                    if (plantillaTbody) {
                        const plantillaTr = plantillaTbody.querySelector('tr');
                        if (plantillaTr) {
                            const nuevoTr = plantillaTr.cloneNode(true);
                            tbodyPadre.appendChild(nuevoTr);
                            const primerInput = nuevoTr.querySelector('input, select, textarea');
                            if (primerInput) {
                                primerInput.focus(); // Pone el cursor automáticamente aquí
                                const btnAnexar = document.getElementById('anexar_articulo');
                                if (btnAnexar) {
                                    btnAnexar.textContent = 'Anexar';
                                }
                            }
                        }
                    }
                }
            }
        });
    }

    // --- NUEVO: LÓGICA PARA ELIMINAR FILAS EN LA TABLA DE FACTURAS ---
    if (tablaFacturas) {
        tablaFacturas.addEventListener('click', (e) => {
            if (e.target && e.target.tagName === 'BUTTON' && e.target.textContent.trim() === '-') {
                e.preventDefault();
                const trPadre = e.target.closest('tr');
                if (trPadre && trPadre.id !== 'factura') {
                    const tbodyPadre = trPadre.closest('tbody');
                    if (tbodyPadre) {
                        const filas = tbodyPadre.querySelectorAll('tr');
                        if (filas.length <= 1) {
                            return; // No eliminar si es la única fila
                        }
                    }
                    // Eliminar los artículos asociados si tiene ID de factura compuesto
                    if (trPadre.id && trPadre.id.startsWith('factura_')) {
                        const tablaArticulos = document.getElementById('tabla_articulos');
                        if (tablaArticulos) {
                            const tbodyArt = tablaArticulos.querySelector(`tbody[factura="${trPadre.id}"]`);
                            if (tbodyArt) tbodyArt.remove();
                        }
                    }
                    trPadre.remove();
                }
            }
        });
    }

    // --- NUEVO: LÓGICA PARA ELIMINAR FILAS EN LA TABLA DE ARTÍCULOS ---
    if (tablaArticulos) {
        tablaArticulos.addEventListener('click', (e) => {
            if (e.target && e.target.tagName === 'BUTTON' && e.target.textContent.trim() === '-') {
                e.preventDefault();
                const trPadre = e.target.closest('tr');
                if (trPadre) {
                    const tbodyPadre = trPadre.closest('tbody');
                    if (tbodyPadre) {
                        if (tbodyPadre.getAttribute('factura') === 'factura') {
                            return; // No eliminar la plantilla
                        }
                        const filas = tbodyPadre.querySelectorAll('tr');
                        if (filas.length <= 1) {
                            return; // No eliminar si es la única fila
                        }
                    }
                    trPadre.remove();
                }
            }
        });
    }

    // --- NUEVO: LÓGICA PARA AGREGAR FILAS EN LA TABLA DE DOCUMENTOS ---
    const tbodyDocumentos = document.getElementById('tabla_documentos');
    if (tbodyDocumentos) {
        tbodyDocumentos.addEventListener('click', (e) => {
            if (e.target && e.target.tagName === 'BUTTON' && e.target.textContent.trim() === '+') {
                e.preventDefault();
                const plantillaTr = document.getElementById('fila_documentos');
                if (plantillaTr) {
                    const nuevoTr = plantillaTr.cloneNode(true);
                    nuevoTr.removeAttribute('id');
                    nuevoTr.style.display = '';
                    tbodyDocumentos.appendChild(nuevoTr);
                }
            }
        });
    }

    // --- NUEVO: LÓGICA PARA ELIMINAR FILAS EN LA TABLA DE DOCUMENTOS ---
    if (tbodyDocumentos) {
        tbodyDocumentos.addEventListener('click', (e) => {
            if (e.target && e.target.tagName === 'BUTTON' && e.target.textContent.trim() === '-') {
                e.preventDefault();
                const trPadre = e.target.closest('tr');
                if (trPadre && trPadre.id !== 'fila_documentos') {
                    const tbodyPadre = trPadre.closest('tbody');
                    if (tbodyPadre) {
                        // Filtramos excluyendo la fila plantilla
                        const filasVisibles = Array.from(tbodyPadre.querySelectorAll('tr')).filter(tr => tr.id !== 'fila_documentos');
                        if (filasVisibles.length <= 1) {
                            return; // No eliminar si es la única fila real
                        }
                    }
                    trPadre.remove();
                }
            }
        });
    }

    // --- NUEVO: ACTUALIZAR EL TEXTO DE LA PESTAÑA (TAB) CON EL PROVEEDOR SELECCIONADO ---
    document.addEventListener('change', function (e) {
        const select = e.target;
        if (select && select.tagName === 'SELECT' && select.name === 'proveedor') {
            // Obtener el bisabuelo (tercer ancestro)
            const parent1 = select.parentElement;
            const parent2 = parent1 ? parent1.parentElement : null;
            const parent3 = parent2 ? parent2.parentElement : null;

            if (parent3 && parent3.id) {
                const id = parent3.id;
                // Buscar el hipervínculo con href igual al id (con o sin #)
                const link = document.querySelector(`a[href="#${id}"], a[href="${id}"]`);
                if (link) {
                    const span = link.querySelector('span');
                    if (span) {
                        const selectedOption = select.options[select.selectedIndex];
                        if (selectedOption) {
                            // Tomar el valor/texto de la opción (priorizando el texto si no está vacío, sino el valor)
                            const optionValue = selectedOption.text.trim() ? selectedOption.text.trim() : selectedOption.value;
                            // Tomar solo los primeros 10 caracteres
                            const truncated = optionValue.substring(0, 10);
                            span.textContent = truncated;
                        }
                    }
                }
            }
        }
    });
});

// --- NUEVO: FUNCIÓN INDEPENDIENTE PARA SINCRONIZAR TABLA DE ARTÍCULOS CON EL DIV DE ARTÍCULOS ---
function inicializarSincronizacionArticulos() {
    const tablaArt = document.getElementById('tabla_articulos');
    const divArt = document.getElementById('articulos');
    if (!tablaArt || !divArt) return;

    const mapeoSimple = {
        'codigo_articulo': 'codigo_articulo',
        'ampliada_articulo': 'ampliada_articulo',
        'pais_articulo': 'pais_de_origen_articulo',
        'regimen_articulo': 'regimen_articulo',
        'sub_regimen_articulo': 'sub_regimen_articulo',
        'preferencia_articulo': 'preferencia_articulo',
        'ceup_articulo': 'ceup_articulo',
        'estado_articulo': 'estado_articulo',
        'bultos_articulo': 'bulto_articulo',
        'embalaje_articulo': 'embalaje_articulo',
        'peso_bruto_articulo': 'peso_bruto_articulo',
        'peso_neto_articulo': 'peso_neto_articulo',
        'cantidad_articulo': 'cantidad_articulo',
        'unidad_de_medida_articulo': 'unidad_de_medida_articulo',
        'unidad_estadistica_articulo': 'unidad_estadistica_articulo',
        'precio_articulo': 'precio_articulo',
        'total_articulo': 'total_articulo',
        'vin_articulo': 'vin_articulo',
        'anio_articulo': 'anio_articulo'
    };

    let filaSeleccionada = null;
    let isMouseDownInside = false;

    // Registrar si el mouse está presionando dentro de la tabla o el div de artículos
    document.addEventListener('mousedown', function (e) {
        if (tablaArt.contains(e.target) || divArt.contains(e.target)) {
            isMouseDownInside = true;
        } else {
            isMouseDownInside = false;
        }
    });

    document.addEventListener('mouseup', function () {
        isMouseDownInside = false;
    });

    function limpiarDivArticulos() {
        // 1. PRIMERO quitamos los estilos visuales y ROMPEMOS la referencia de la fila
        if (filaSeleccionada) {
            filaSeleccionada.classList.remove('table-active');
            filaSeleccionada.style.backgroundColor = '';

            // CRÍTICO: Convertimos la variable en null ANTES de vaciar los inputs.
            // Así, los eventos de sincronización ignorarán la tabla porque ya no habrá fila activa.
            filaSeleccionada = null;
        }

        // Cambiar el texto del botón a "Anexar"
        const btnAnexar = document.getElementById('anexar_articulo');
        if (btnAnexar) {
            btnAnexar.textContent = 'Anexar';
        }

        // 2. SEGUNDO limpiamos los inputs de forma segura
        const inputsAndSelects = divArt.querySelectorAll('input, select, textarea');
        inputsAndSelects.forEach(el => {
            if (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
                if (el.value !== '') {
                    el.value = '';
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else {
                if (el.textContent !== '') {
                    el.textContent = '';
                }
            }
        });
    }

    function actualizarInformacionArticuloVisibilidad() {
        const elDivCodigo = divArt.querySelector('[name="codigo_articulo"]');
        const elDivInfo = divArt.querySelector('[name="informacion_articulo"]');
        if (!elDivInfo) return;

        const codigoVacio = !elDivCodigo || !elDivCodigo.value.trim();
        let valorInfo = '';

        if (!codigoVacio && filaSeleccionada) {
            const camposInfo = [
                'nombre_comercial_articulo',
                'descripcion_articulo',
                'partida_articulo',
                'marca_articulo',
                'modelo_articulo'
            ];
            const valoresInfo = camposInfo.map(name => {
                const el = filaSeleccionada.querySelector(`[name="${name}"]`);
                if (el) {
                    if (el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA') {
                        return el.value;
                    }
                    return el.textContent || '';
                }
                return '';
            });
            valorInfo = valoresInfo.join('::');
        }

        if (elDivInfo.tagName === 'INPUT' || elDivInfo.tagName === 'SELECT' || elDivInfo.tagName === 'TEXTAREA') {
            if (elDivInfo.value !== valorInfo) {
                elDivInfo.value = valorInfo;
                elDivInfo.dispatchEvent(new Event('input', { bubbles: true }));
                elDivInfo.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } else {
            if (elDivInfo.textContent !== valorInfo) {
                elDivInfo.textContent = valorInfo;
            }
        }
    }

    function actualizarDivArticulos(row) {
        if (!row) return;

        // Mapeos simples
        for (const [nameTabla, nameDiv] of Object.entries(mapeoSimple)) {
            let valor = '';
            const elTabla = row.querySelector(`[name="${nameTabla}"]`);
            if (elTabla) {
                if (elTabla.tagName === 'INPUT' || elTabla.tagName === 'SELECT' || elTabla.tagName === 'TEXTAREA') {
                    valor = elTabla.value;
                } else {
                    valor = elTabla.textContent || '';
                }
            }

            const elDiv = divArt.querySelector(`[name="${nameDiv}"]`);
            if (elDiv) {
                if (elDiv.tagName === 'INPUT' || elDiv.tagName === 'SELECT' || elDiv.tagName === 'TEXTAREA') {
                    if (elDiv.value !== valor) {
                        elDiv.value = valor;
                        elDiv.dispatchEvent(new Event('input', { bubbles: true }));
                        elDiv.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                } else {
                    if (elDiv.textContent !== valor) {
                        elDiv.textContent = valor;
                    }
                }
            }
        }

        // RGO-A y RGO-B (duplicados de nombre name="rgo-a_articulo" en la tabla)
        const rgoAElements = row.querySelectorAll('[name="rgo-a_articulo"]');
        let rgoAValue = '';
        let rgoBValue = '';
        if (rgoAElements.length > 0) {
            rgoAValue = rgoAElements[0].value;
        }
        if (rgoAElements.length > 1) {
            rgoBValue = rgoAElements[1].value;
        } else {
            const rgoBElement = row.querySelector('[name="rgo-b_articulo"]');
            if (rgoBElement) {
                rgoBValue = rgoBElement.value;
            }
        }

        const elDivRgoA = divArt.querySelector('[name="rgo-a_articulo"]');
        if (elDivRgoA) {
            if (elDivRgoA.tagName === 'INPUT' || elDivRgoA.tagName === 'SELECT' || elDivRgoA.tagName === 'TEXTAREA') {
                if (elDivRgoA.value !== rgoAValue) {
                    elDivRgoA.value = rgoAValue;
                    elDivRgoA.dispatchEvent(new Event('input', { bubbles: true }));
                    elDivRgoA.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else {
                if (elDivRgoA.textContent !== rgoAValue) {
                    elDivRgoA.textContent = rgoAValue;
                }
            }
        }

        const elDivRgoB = divArt.querySelector('[name="rgo-b_articulo"]');
        if (elDivRgoB) {
            if (elDivRgoB.tagName === 'INPUT' || elDivRgoB.tagName === 'SELECT' || elDivRgoB.tagName === 'TEXTAREA') {
                if (elDivRgoB.value !== rgoBValue) {
                    elDivRgoB.value = rgoBValue;
                    elDivRgoB.dispatchEvent(new Event('input', { bubbles: true }));
                    elDivRgoB.dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else {
                if (elDivRgoB.textContent !== rgoBValue) {
                    elDivRgoB.textContent = rgoBValue;
                }
            }
        }

        // Concatenado para informacion_articulo (condicionado a que codigo_articulo no esté vacío)
        actualizarInformacionArticuloVisibilidad();
    }

    function seleccionarFila(row) {
        if (filaSeleccionada) {
            filaSeleccionada.classList.remove('table-active');
            filaSeleccionada.style.backgroundColor = '';
        }
        filaSeleccionada = row;
        if (filaSeleccionada) {
            filaSeleccionada.classList.add('table-active');
            filaSeleccionada.style.backgroundColor = 'rgba(63, 114, 175, 0.12)';

            // Cambiar el texto del botón a "Actualizar"
            const btnAnexar = document.getElementById('anexar_articulo');
            if (btnAnexar) {
                btnAnexar.textContent = 'Actualizar';
            }
        }
    }

    const handleSelection = function (e) {
        const target = e.target;
        const isInputOrSelect = (target.tagName === 'INPUT' && target.type === 'text') || target.tagName === 'SELECT';
        if (isInputOrSelect) {
            const tr = target.closest('tr');
            if (tr) {
                const tbody = tr.closest('tbody');
                if (tbody && tbody.getAttribute('factura') === 'factura') {
                    return; // Omitir fila de plantilla
                }
                seleccionarFila(tr);
                actualizarDivArticulos(tr);
            }
        }
    };

    tablaArt.addEventListener('click', handleSelection);
    tablaArt.addEventListener('focusin', handleSelection);
    tablaArt.addEventListener('input', handleSelection);
    tablaArt.addEventListener('change', handleSelection);

    // Quitar el foco de cualquier elemento de la tabla
    tablaArt.addEventListener('focusout', function (e) {
        setTimeout(() => {
            const activeEl = document.activeElement;
            // Si el foco ya no está en la tabla ni en el div de artículos, y el usuario no está haciendo clic dentro de ellos, limpiamos
            if (!tablaArt.contains(activeEl) && !divArt.contains(activeEl) && !isMouseDownInside) {
                limpiarDivArticulos();
            }
        }, 50);
    });

    // Sincronización Div -> Tabla (edición en div actualiza la fila seleccionada)
    divArt.addEventListener('input', function (e) {
        if (!filaSeleccionada) return;
        const target = e.target;
        const nameDiv = target.name;
        if (!nameDiv) return;

        const nameTabla = Object.keys(mapeoSimple).find(key => mapeoSimple[key] === nameDiv);
        if (nameTabla) {
            const elTabla = filaSeleccionada.querySelector(`[name="${nameTabla}"]`);
            if (elTabla && elTabla.value !== target.value) {
                elTabla.value = target.value;
                elTabla.dispatchEvent(new Event('input', { bubbles: true }));
                elTabla.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } else if (nameDiv === 'rgo-a_articulo') {
            const rgoAElements = filaSeleccionada.querySelectorAll('[name="rgo-a_articulo"]');
            if (rgoAElements.length > 0 && rgoAElements[0].value !== target.value) {
                rgoAElements[0].value = target.value;
                rgoAElements[0].dispatchEvent(new Event('input', { bubbles: true }));
                rgoAElements[0].dispatchEvent(new Event('change', { bubbles: true }));
            }
        } else if (nameDiv === 'rgo-b_articulo') {
            const rgoAElements = filaSeleccionada.querySelectorAll('[name="rgo-a_articulo"]');
            if (rgoAElements.length > 1) {
                if (rgoAElements[1].value !== target.value) {
                    rgoAElements[1].value = target.value;
                    rgoAElements[1].dispatchEvent(new Event('input', { bubbles: true }));
                    rgoAElements[1].dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else {
                const rgoBElement = filaSeleccionada.querySelector('[name="rgo-b_articulo"]');
                if (rgoBElement && rgoBElement.value !== target.value) {
                    rgoBElement.value = target.value;
                    rgoBElement.dispatchEvent(new Event('input', { bubbles: true }));
                    rgoBElement.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        }

        // Si se editó el código de artículo en el div, verificar visibilidad de la info
        if (nameDiv === 'codigo_articulo') {
            actualizarInformacionArticuloVisibilidad();
        }
    });

    divArt.addEventListener('change', function (e) {
        if (!filaSeleccionada) return;
        const target = e.target;
        const nameDiv = target.name;
        if (!nameDiv) return;

        const nameTabla = Object.keys(mapeoSimple).find(key => mapeoSimple[key] === nameDiv);
        if (nameTabla) {
            const elTabla = filaSeleccionada.querySelector(`[name="${nameTabla}"]`);
            if (elTabla && elTabla.value !== target.value) {
                elTabla.value = target.value;
                elTabla.dispatchEvent(new Event('change', { bubbles: true }));
            }
        } else if (nameDiv === 'rgo-a_articulo') {
            const rgoAElements = filaSeleccionada.querySelectorAll('[name="rgo-a_articulo"]');
            if (rgoAElements.length > 0 && rgoAElements[0].value !== target.value) {
                rgoAElements[0].value = target.value;
                rgoAElements[0].dispatchEvent(new Event('change', { bubbles: true }));
            }
        } else if (nameDiv === 'rgo-b_articulo') {
            const rgoAElements = filaSeleccionada.querySelectorAll('[name="rgo-a_articulo"]');
            if (rgoAElements.length > 1) {
                if (rgoAElements[1].value !== target.value) {
                    rgoAElements[1].value = target.value;
                    rgoAElements[1].dispatchEvent(new Event('change', { bubbles: true }));
                }
            } else {
                const rgoBElement = filaSeleccionada.querySelector('[name="rgo-b_articulo"]');
                if (rgoBElement && rgoBElement.value !== target.value) {
                    rgoBElement.value = target.value;
                    rgoBElement.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        }

        // Si se cambió el código de artículo en el div, verificar visibilidad de la info
        if (nameDiv === 'codigo_articulo') {
            actualizarInformacionArticuloVisibilidad();
        }
    });

    // --- NUEVO: EVENTO PARA EL BOTÓN ANEXAR ARTÍCULO ---
    const btnAnexar = document.getElementById('anexar_articulo');
    if (btnAnexar) {
        btnAnexar.addEventListener('click', function (e) {
            e.preventDefault();

            if (btnAnexar.textContent.trim() === 'Actualizar') {
                // --- MODO ACTUALIZAR ---
                if (!filaSeleccionada) return;

                // Copiar los valores desde el div#articulos hacia la fila seleccionada usando mapeoSimple
                for (const [nameTabla, nameDiv] of Object.entries(mapeoSimple)) {
                    const elDiv = divArt.querySelector(`[name="${nameDiv}"]`);
                    const elTabla = filaSeleccionada.querySelector(`[name="${nameTabla}"]`);
                    if (elDiv && elTabla) {
                        let valor = '';
                        if (elDiv.tagName === 'INPUT' || elDiv.tagName === 'SELECT' || elDiv.tagName === 'TEXTAREA') {
                            valor = elDiv.value;
                        } else {
                            valor = elDiv.textContent || '';
                        }

                        if (elTabla.tagName === 'INPUT' || elTabla.tagName === 'SELECT' || elTabla.tagName === 'TEXTAREA') {
                            elTabla.value = valor;
                        } else {
                            elTabla.textContent = valor;
                        }
                    }
                }

                // Desglosar informacion_articulo (los campos individuales que no están en mapeoSimple)
                const elDivInfo = divArt.querySelector('[name="informacion_articulo"]');
                if (elDivInfo) {
                    const infoVal = elDivInfo.value || '';
                    if (infoVal.trim() !== '') {
                        const partes = infoVal.split('::');
                        const camposInfo = [
                            'nombre_comercial_articulo',
                            'descripcion_articulo',
                            'partida_articulo',
                            'marca_articulo',
                            'modelo_articulo'
                        ];
                        camposInfo.forEach((name, idx) => {
                            const elTabla = filaSeleccionada.querySelector(`[name="${name}"]`);
                            if (elTabla && partes[idx] !== undefined) {
                                elTabla.value = partes[idx];
                            }
                        });
                    }
                }

                // Copiar RGO-A y RGO-B que tampoco están en mapeoSimple
                const elDivRgoA = divArt.querySelector('[name="rgo-a_articulo"]');
                if (elDivRgoA) {
                    const rgoAElements = filaSeleccionada.querySelectorAll('[name="rgo-a_articulo"]');
                    if (rgoAElements.length > 0) {
                        rgoAElements[0].value = elDivRgoA.value;
                    }
                }
                const elDivRgoB = divArt.querySelector('[name="rgo-b_articulo"]');
                if (elDivRgoB) {
                    const rgoAElements = filaSeleccionada.querySelectorAll('[name="rgo-a_articulo"]');
                    if (rgoAElements.length > 1) {
                        rgoAElements[1].value = elDivRgoB.value;
                    } else {
                        const rgoBElement = filaSeleccionada.querySelector('[name="rgo-b_articulo"]');
                        if (rgoBElement) {
                            rgoBElement.value = elDivRgoB.value;
                        }
                    }
                }

                // Disparar eventos de input y change en los elementos de la fila seleccionada
                filaSeleccionada.querySelectorAll('input, select, textarea').forEach(el => {
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                });

                // Limpiar el div de artículos (resetea los inputs, remueve la selección visual y vuelve a "Anexar")
                limpiarDivArticulos();

            } else {
                // --- MODO ANEXAR ---
                const plantillaTbody = document.querySelector('tbody[factura="factura"]');
                if (!plantillaTbody) return;

                const plantillaTr = plantillaTbody.querySelector('tr');
                if (!plantillaTr) return;

                // Encontrar el tbody activo (con atributo factura que no tenga style="display:none;")
                const activeTbody = Array.from(document.querySelectorAll('tbody[factura]')).find(tbody => {
                    return tbody.getAttribute('factura') !== 'factura' && tbody.style.display !== 'none';
                });

                if (!activeTbody) return;

                // Clonar la fila de la plantilla
                const nuevoTr = plantillaTr.cloneNode(true);

                // Copiar los valores desde el div#articulos hacia el nuevoTr usando mapeoSimple
                for (const [nameTabla, nameDiv] of Object.entries(mapeoSimple)) {
                    const elDiv = divArt.querySelector(`[name="${nameDiv}"]`);
                    const elTabla = nuevoTr.querySelector(`[name="${nameTabla}"]`);
                    if (elDiv && elTabla) {
                        let valor = '';
                        if (elDiv.tagName === 'INPUT' || elDiv.tagName === 'SELECT' || elDiv.tagName === 'TEXTAREA') {
                            valor = elDiv.value;
                        } else {
                            valor = elDiv.textContent || '';
                        }

                        if (elTabla.tagName === 'INPUT' || elTabla.tagName === 'SELECT' || elTabla.tagName === 'TEXTAREA') {
                            elTabla.value = valor;
                        } else {
                            elTabla.textContent = valor;
                        }
                    }
                }

                // Desglosar informacion_articulo (los campos individuales que no están en mapeoSimple)
                const elDivInfo = divArt.querySelector('[name="informacion_articulo"]');
                if (elDivInfo) {
                    const infoVal = elDivInfo.value || '';
                    if (infoVal.trim() !== '') {
                        const partes = infoVal.split('::');
                        const camposInfo = [
                            'nombre_comercial_articulo',
                            'descripcion_articulo',
                            'partida_articulo',
                            'marca_articulo',
                            'modelo_articulo'
                        ];
                        camposInfo.forEach((name, idx) => {
                            const elTabla = nuevoTr.querySelector(`[name="${name}"]`);
                            if (elTabla && partes[idx] !== undefined) {
                                elTabla.value = partes[idx];
                            }
                        });
                    }
                }

                // Copiar RGO-A y RGO-B que tampoco están en mapeoSimple
                const elDivRgoA = divArt.querySelector('[name="rgo-a_articulo"]');
                if (elDivRgoA) {
                    const rgoAElements = nuevoTr.querySelectorAll('[name="rgo-a_articulo"]');
                    if (rgoAElements.length > 0) {
                        rgoAElements[0].value = elDivRgoA.value;
                    }
                }
                const elDivRgoB = divArt.querySelector('[name="rgo-b_articulo"]');
                if (elDivRgoB) {
                    const rgoAElements = nuevoTr.querySelectorAll('[name="rgo-a_articulo"]');
                    if (rgoAElements.length > 1) {
                        rgoAElements[1].value = elDivRgoB.value;
                    } else {
                        const rgoBElement = nuevoTr.querySelector('[name="rgo-b_articulo"]');
                        if (rgoBElement) {
                            rgoBElement.value = elDivRgoB.value;
                        }
                    }
                }

                // Anexar la fila clonada al final del tbody activo
                activeTbody.appendChild(nuevoTr);

                // Disparar eventos de input y change en los elementos del nuevoTr para asegurar la propagación
                nuevoTr.querySelectorAll('input, select, textarea').forEach(el => {
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                });

                // Limpiar el div de artículos (resetea los inputs y remueve la selección visual)
                limpiarDivArticulos();
            }
        });
    }
}

// --- NAVEGACIÓN LATERAL LIMPIA Y SCROLL-SPY ---
function inicializarNavegacionYSpy() {
    const sidebarLinks = document.querySelectorAll('aside .nav-link');
    const idsSecciones = Array.from(document.querySelectorAll("[id^='sec-']"));

    // 1. Clic en la barra lateral: desplazamiento suave sin alterar la URL (#hash)
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();

            const targetId = link.getAttribute('href');
            if (targetId && targetId.startsWith('#')) {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }

            // Actualizar resaltado visual
            sidebarLinks.forEach(l => {
                l.classList.remove('active');
                l.classList.add('text-white');
            });
            link.classList.add('active');
            link.classList.remove('text-white');
        });
    });

    // 2. IntersectionObserver: actualiza automáticamente el menú según el scroll
    if (idsSecciones.length > 0) {
        const opcionesObserver = {
            root: null,
            rootMargin: '-20% 0px -70% 0px',
            threshold: 0
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const idActual = entry.target.getAttribute('id');

                    sidebarLinks.forEach((enlace) => {
                        enlace.classList.remove('active');
                        enlace.classList.add('text-white');
                    });

                    const enlaceActivo = document.querySelector(`aside .nav-link[href="#${idActual}"]`);
                    if (enlaceActivo) {
                        enlaceActivo.classList.add('active');
                        enlaceActivo.classList.remove('text-white');
                    }
                }
            });
        }, opcionesObserver);

        idsSecciones.forEach((seccion) => observer.observe(seccion));
    }
}

// Ejecución garantizada
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarNavegacionYSpy);
    document.addEventListener('DOMContentLoaded', inicializarSincronizacionArticulos);
} else {
    inicializarNavegacionYSpy();
    inicializarSincronizacionArticulos();
}