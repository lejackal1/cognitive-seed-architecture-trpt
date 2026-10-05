# 00_sistema_kpis_ospost.md — Sistema de Metricas e Indicadores OSPOST AI

## Proposito

Medir, controlar y mejorar el rendimiento del sistema OSPOST AI mediante indicadores cuantitativos y cualitativos.

Sin metricas no hay hiperautomatizacion medible.

---

## 🔷 Dimensiones de medicion

```text
1. Calidad de analisis
2. Memoria
3. Casuistica
4. Sistema
5. Evolucion
```

---

## 🔹 1. Calidad de analisis

### KPI-001: % procesos con trazabilidad completa

**Definicion:**
Procesos documentados que incluyen las 6 capas TPRT / total de procesos documentados.

**Formula:**
```text
(trazabilidad_completa / procesos_documentados) * 100
```

**Meta:** >= 95%

**Frecuencia:** por modulo

**Registro:**
```text
.ai/metricas/kpi_001_trazabilidad.md
```

---

### KPI-002: % procesos con evidencia cruzada

**Definicion:**
Procesos con evidencia en >= 3 capas (Vista + Controller + BD) / total de procesos.

**Formula:**
```text
(evidencia_cruzada / procesos_documentados) * 100
```

**Meta:** >= 90%

**Frecuencia:** por modulo

---

### KPI-003: % inconsistencias detectadas

**Definicion:**
Inconsistencias encontradas entre capas / total de procesos analizados.

**Formula:**
```text
(inconsistencias / procesos_analizados) * 100
```

**Meta:** <= 10% (objetivo: tendencia a la baja)

**Frecuencia:** por modulo

---

## 🔹 2. Memoria

### KPI-004: % documentacion integrada en memoria

**Definicion:**
Documentos validados por (09) que fueron integrados en (08) / total de documentos validados.

**Formula:**
```text
(documentos_integrados / documentos_validados) * 100
```

**Meta:** 100%

**Frecuencia:** por ciclo de integracion

---

### KPI-005: % duplicacion eliminada

**Definicion:**
Registros consolidados (merge) / registros que requirieron comparacion.

**Formula:**
```text
(consolidados / comparados) * 100
```

**Meta:** >= 80%

**Frecuencia:** por ciclo de integracion

---

### KPI-006: Crecimiento de base de conocimiento

**Definicion:**
Numero de registros nuevos en memoria por periodo.

**Formula:**
```text
registros_nuevos(modulos) + registros_nuevos(procesos) + registros_nuevos(patrones) + registros_nuevos(casuisticas)
```

**Meta:** crecimiento sostenido > 0

**Frecuencia:** mensual

---

## 🔹 3. Casuistica

### KPI-007: Numero de casuisticas detectadas por modulo

**Definicion:**
Casuisticas creadas en `/casuistica/` asociadas a un modulo.

**Formula:**
```text
conteo de archivos .md en /casuistica/ por modulo
```

**Meta:** variable (indica riqueza del dominio)

**Frecuencia:** por modulo

---

### KPI-008: % casuisticas promovidas a proceso

**Definicion:**
Casuisticas que pasaron a /procesos/ / total de casuisticas evaluadas.

**Formula:**
```text
(promovidas / evaluadas) * 100
```

**Meta:** <= 20% (mayoria debe permanecer como variacion)

**Frecuencia:** trimestral

---

### KPI-009: % casuisticas rechazadas

**Definicion:**
Casuisticas clasificadas como rechazadas / total evaluadas.

**Formula:**
```text
(rechazadas / evaluadas) * 100
```

**Meta:** <= 15%

**Frecuencia:** trimestral

---

## 🔹 4. Sistema

### KPI-010: Tiempo de analisis por modulo

**Definicion:**
Duracion desde inicio de investigacion hasta entrega de checklist.

**Formula:**
```text
tiempo_final - tiempo_inicio (en minutos)
```

**Meta:** <= 120 minutos por modulo estandar

**Frecuencia:** por modulo

---

### KPI-011: Tiempo de generacion de documentacion

**Definicion:**
Duracion desde checklist hasta entrega de documento tecnico + usuario final.

**Formula:**
```text
tiempo_doc_final - tiempo_checklist (en minutos)
```

**Meta:** <= 90 minutos por proceso

**Frecuencia:** por proceso

---

### KPI-012: Tiempo de generacion de codigo

**Definicion:**
Duracion desde activacion del generador (11) hasta entrega de codigo validable.

**Formula:**
```text
tiempo_codigo_entregado - tiempo_activacion (en minutos)
```

**Meta:** <= 60 minutos por modulo

**Frecuencia:** por modulo generado

---

## 🔹 5. Evolucion

### KPI-013: % reutilizacion de procesos

**Definicion:**
Procesos que reutilizan logica de memoria existente / total de procesos nuevos.

**Formula:**
```text
(procesos_reutilizados / procesos_nuevos) * 100
```

**Meta:** >= 60%

**Frecuencia:** mensual

---

### KPI-014: Reduccion de errores por conocimiento previo

**Definicion:**
Inconsistencias detectadas en modulos con memoria previa vs. sin memoria.

**Formula:**
```text
(inconsistencias_sin_memoria - inconsistencias_con_memoria) / inconsistencias_sin_memoria * 100
```

**Meta:** >= 40% de reduccion

**Frecuencia:** mensual

---

### KPI-015: Coherencia entre versiones del sistema

**Definicion:**
Procesos documentados cuya memoria coincide con codigo actual / total de procesos en memoria.

**Formula:**
```text
(coherentes / total_en_memoria) * 100
```

**Meta:** >= 95%

**Frecuencia:** semanal (auditoria)

---

### KPI-016: Ratio contexto bootstrap / sesion M4

**Definicion:**
Tokens (o estimacion de caracteres de MD cargados en bootstrap) / tokens totales estimados de la sesion M4.

**Formula:**
```text
(chars_bootstrap / chars_sesion_estimados) * 100
```

**Meta:** tendencia decreciente sin caer KPI-001 bajo 95%

**Frecuencia:** por modulo piloto / por cierre DEV

**Registro:**
```text
.ai/metricas/kpi_016_contexto/
```

**Rollback:** si KPI-001 < 95% en mismo modulo → `@ECONOMIA:BUILD=OFF`

---

### KPI-017: LOC anadidas en diff build

**Definicion:**
Lineas anadidas (`git diff` stat) en entrega agente 11 vs baseline historico del mismo tipo de ticket en el modulo.

**Formula:**
```text
loc_diff_sesion_actual vs mediana loc_diff_historico
```

**Meta:** tendencia decreciente; no por debajo de cobertura TPRT (KPI-001)

**Frecuencia:** por cierre DEV con economia build activa

**Registro:**
```text
.ai/metricas/kpi_017_diff/
```

---

## 🔒 Reglas de medicion

1. **Toda metrica requiere evidencia:** fecha, modulo, agente, resultado
2. **Sin registro no existe:** toda medicion debe persistir en `.ai/metricas/`
3. **Tendencia sobre punto:** se evalua la tendencia, no un valor aislado
4. **Umbral de alerta:** si un KPI cae bajo meta por 3 ciclos consecutivos, activar auditoria
5. **Integracion automatica:** los agentes (04, 08, 09, 11) DEBEN registrar metricas en cada ejecucion

---

## 📊 Formato de registro

```md
# Metrica: [KPI-NNN]

## Periodo:
[fecha_inicio] - [fecha_fin]

## Modulo:
[nombre]

## Agente:
[responsable]

## Valor:
[numero]

## Meta:
[numero]

## Estado:
- Cumple
- No cumple
- Alerta

## Observaciones:
- ...

## Ruta de evidencia:
[archivo de soporte]
```

---

## 🔁 Flujo de medicion

```text
Ejecucion de agente
↓
Registro de metricas (auto)
↓
Persistencia en .ai/metricas/
↓
Evaluacion de tendencia
↓
Alerta si es necesario
↓
Accion correctiva
```

---

## 🔒 Acciones automaticas por umbral

### Si baja la cobertura de trazabilidad

- activar auditoria del modulo afectado;
- re-ejecutar investigacion tecnica;
- bloquear promocion a memoria hasta corregir cobertura.

### Si aumenta la duplicacion

- revisar memoria existente;
- comparar procesos similares;
- consolidar o rechazar registros redundantes.

### Si cae la coherencia entre versiones

- bloquear generacion de codigo;
- revisar casuistica y patrones afectados;
- forzar validacion de calidad.

### Si cae la reutilizacion

- revisar patrones comunes;
- detectar ausencia de memoria previa;
- reforzar integración de conocimiento.

### Si el crecimiento de conocimiento es nulo

- auditar entrada y persistencia;
- revisar fallos de clasificación;
- verificar si el sistema está rechazando evidencia válida.

---

## 📚 Colector persistente e historico de metricas

Las metricas deben persistirse en base de datos como eventos historicos para permitir comparacion, tendencia y auditoria; la carpeta `.ai/metricas/` actua como indice documental del historico.

### Campos mínimos por registro

- KPI identificado;
- modulo afectado;
- periodo de medicion;
- valor obtenido;
- meta esperada;
- umbral aplicado;
- accion disparada;
- estado (cumple / no cumple / alerta);
- fecha y hora;
- evidencia de soporte;
- referencia al evento o ledger que la originó.

### Regla operativa

- no sobrescribir registros historicos;
- cada ejecucion de KPI debe quedar en el historial;
- el motor de accion debe leer el histórico para detectar tendencias, no solo valores aislados;
- cuando un umbral dispare una accion, esta debe registrarse como evento de control.

---

## Referencias transversales

- Ver: `00_metodologia_ospost_ai.md` (Fase 7 — Control de evolucion)
- Ver: `08_agent_memoria_ospost.md` (Integracion automatica)
- Ver: `09_agent_evaluador_calidad_ospost.md` (Validacion)
