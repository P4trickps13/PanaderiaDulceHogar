document.addEventListener("DOMContentLoaded", function () {
    const ventasCanvas = document.getElementById("ventasChart");
    const productosCanvas = document.getElementById("productosChart");
    const datosElemento = document.getElementById("dashboardDatos");

    if (!ventasCanvas || !productosCanvas || !datosElemento) {
        return;
    }

    let datos = { ventas_fecha: {}, productos: {} };
    let graficoVentas = null;
    let graficoProductos = null;
    let tipoVentas = "line";

    const filtroVentas = document.getElementById("filtroVentas");
    const limiteProductos = document.getElementById("limiteProductos");
    const cambiarTipoVentas = document.getElementById("cambiarTipoVentas");
    const actualizarGraficos = document.getElementById("actualizarGraficos");
    const estadoGraficos = document.getElementById("estadoGraficos");

    try {
        datos = JSON.parse(datosElemento.textContent);
    } catch (error) {
        mostrarEstado("No se pudieron leer los datos iniciales.", true);
    }

    function mostrarEstado(mensaje, esError = false) {
        if (!estadoGraficos) {
            return;
        }
        estadoGraficos.textContent = mensaje;
        estadoGraficos.classList.toggle("error", esError);
    }

    function mostrarAviso(canvas, avisoId, mensaje) {
        canvas.hidden = true;
        const aviso = document.getElementById(avisoId);
        if (aviso) {
            aviso.textContent = mensaje;
            aviso.hidden = false;
        }
    }

    function ocultarAviso(canvas, avisoId) {
        canvas.hidden = false;
        const aviso = document.getElementById(avisoId);
        if (aviso) {
            aviso.hidden = true;
        }
    }

    function formatoMoneda(valor) {
        return new Intl.NumberFormat("es-PE", {
            style: "currency",
            currency: "PEN",
            minimumFractionDigits: 2
        }).format(valor);
    }

    function filtrarVentas(registros, periodo) {
        const ordenados = Object.entries(registros || {})
            .map(([fecha, total]) => [fecha, Number(total)])
            .filter(([, total]) => Number.isFinite(total))
            .sort((a, b) => a[0].localeCompare(b[0]));

        if (periodo === "all" || ordenados.length === 0) {
            return ordenados;
        }

        const ultimaFecha = new Date(`${ordenados[ordenados.length - 1][0]}T00:00:00`);
        const desde = new Date(ultimaFecha);
        desde.setDate(desde.getDate() - (Number(periodo) - 1));

        return ordenados.filter(([fecha]) => new Date(`${fecha}T00:00:00`) >= desde);
    }

    function limitarProductos(registros, limite) {
        const ordenados = Object.entries(registros || {})
            .map(([nombre, cantidad]) => [nombre, Number(cantidad)])
            .filter(([, cantidad]) => Number.isFinite(cantidad))
            .sort((a, b) => b[1] - a[1]);

        return limite === "all" ? ordenados : ordenados.slice(0, Number(limite));
    }

    function crearGraficoVentas() {
        const periodo = filtroVentas ? filtroVentas.value : "all";
        const registros = filtrarVentas(datos.ventas_fecha, periodo);
        const etiquetas = registros.map(([fecha]) => fecha);
        const valores = registros.map(([, total]) => total);

        if (graficoVentas) {
            graficoVentas.destroy();
            graficoVentas = null;
        }

        if (etiquetas.length === 0) {
            mostrarAviso(ventasCanvas, "ventasSinDatos", "No existen ventas pagadas para graficar.");
            return;
        }
        if (typeof Chart === "undefined") {
            mostrarAviso(
                ventasCanvas,
                "ventasSinDatos",
                "No se pudo cargar la librería local de gráficos. Verifica la carpeta static/js."
            );
            return;
        }

        ocultarAviso(ventasCanvas, "ventasSinDatos");
        graficoVentas = new Chart(ventasCanvas, {
            type: tipoVentas,
            data: {
                labels: etiquetas,
                datasets: [{
                    label: "Ventas pagadas",
                    data: valores,
                    borderWidth: 3,
                    pointRadius: tipoVentas === "line" ? 5 : 0,
                    pointHoverRadius: 8,
                    borderRadius: tipoVentas === "bar" ? 6 : 0,
                    tension: 0.25,
                    fill: tipoVentas === "line"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 700 },
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: { display: true, position: "bottom" },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function (context) {
                                return ` Ventas: ${formatoMoneda(context.parsed.y)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (valor) {
                                return formatoMoneda(valor);
                            }
                        }
                    }
                }
            }
        });
    }

    function crearGraficoProductos() {
        const limite = limiteProductos ? limiteProductos.value : "10";
        const registros = limitarProductos(datos.productos, limite);
        const etiquetas = registros.map(([nombre]) => nombre);
        const valores = registros.map(([, cantidad]) => cantidad);

        if (graficoProductos) {
            graficoProductos.destroy();
            graficoProductos = null;
        }

        if (etiquetas.length === 0) {
            mostrarAviso(
                productosCanvas,
                "productosSinDatos",
                "No existen productos vendidos para graficar."
            );
            return;
        }
        if (typeof Chart === "undefined") {
            mostrarAviso(
                productosCanvas,
                "productosSinDatos",
                "No se pudo cargar la librería local de gráficos. Verifica la carpeta static/js."
            );
            return;
        }

        ocultarAviso(productosCanvas, "productosSinDatos");
        graficoProductos = new Chart(productosCanvas, {
            type: "bar",
            data: {
                labels: etiquetas,
                datasets: [{
                    label: "Unidades vendidas",
                    data: valores,
                    borderWidth: 2,
                    borderRadius: 6,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 700 },
                interaction: { mode: "nearest", intersect: true },
                plugins: {
                    legend: { display: true, position: "bottom" },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function (context) {
                                return ` ${context.parsed.y} unidades`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });
    }

    function renderizarGraficos() {
        crearGraficoVentas();
        crearGraficoProductos();
    }

    if (filtroVentas) {
        filtroVentas.addEventListener("change", crearGraficoVentas);
    }
    if (limiteProductos) {
        limiteProductos.addEventListener("change", crearGraficoProductos);
    }
    if (cambiarTipoVentas) {
        cambiarTipoVentas.addEventListener("click", function () {
            tipoVentas = tipoVentas === "line" ? "bar" : "line";
            cambiarTipoVentas.textContent = tipoVentas === "line" ? "Ver como barras" : "Ver como línea";
            crearGraficoVentas();
        });
    }
    if (actualizarGraficos) {
        actualizarGraficos.addEventListener("click", async function () {
            const url = actualizarGraficos.dataset.url;
            actualizarGraficos.disabled = true;
            mostrarEstado("Actualizando datos...");
            try {
                const respuesta = await fetch(url, {
                    headers: { Accept: "application/json" }
                });
                if (!respuesta.ok) {
                    throw new Error("Respuesta no válida");
                }
                datos = await respuesta.json();
                renderizarGraficos();
                mostrarEstado(`Datos actualizados a las ${new Date().toLocaleTimeString("es-PE")}.`);
            } catch (error) {
                mostrarEstado("No se pudieron actualizar los gráficos.", true);
            } finally {
                actualizarGraficos.disabled = false;
            }
        });
    }

    renderizarGraficos();
});
