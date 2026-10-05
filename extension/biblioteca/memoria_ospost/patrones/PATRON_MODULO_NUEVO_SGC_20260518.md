# Patrón — Alta de módulo nuevo OSPOST (evidencia 2026-05-18)

## Checklist TPRT obligatorio

1. `osp_pre/Modulos/{Modulo}/Controllers/require.php`
2. `osp_pre/Modulos/{Modulo}/Controllers/enviar.php` (switch POST → api_dexcom)
3. `osp_pre/Modulos/{Modulo}/Views/menu.php` (hashes ?r=&m=)
4. `osp_pre/Modulos/{Modulo}/Views/{modulo}_*.php` + `Js/` si aplica
5. `api_pre/Views/{Modulo}/*.php` (orquestación, tipo en switch)
6. `api_dba_pre/Views/{Modulo}/*.php` (PDO, tablas)
7. Registro en `api_pre/Models/config.php` → `ALLOWED_MODULES`
8. Filas en `permisos` + asignación roles (Principal/permisos)
9. Menú sistema / módulos en BD (vía login → iniciar_rolles)

## Contrato api_dexcom

```php
$os->api_dexcom([
    'tipo' => '1|2|3|4|5|...',  // CRUD / operación
    'modulo' => '{Modulo}',      // PascalCase = carpeta Views
    'pagina' => '{snake_case}',  // archivo sin .php
    // campos negocio...
]);
```

## Tipos habituales

| tipo | Uso típico |
|------|------------|
| 1 | listar / read |
| 2 | obtener uno / secuencia |
| 3 | insert |
| 4 | update |
| 5 | delete lógico |

## Referencias módulo mediano

- **Mto:** `osp_pre/Modulos/Mto/` — CRUD OTs, enviar.php extenso
- **Documental:** memoria en `.ai/memoria_ospost/modulos/DOCUMENTAL.md`
- **Transporte:** API extensa (~150 endpoints api_pre); osp parcial

## Integraciones frecuentes

- Principal (people, terceros, municipios)
- Tesorería / Facturación / Contable (comprobantes)
- Bascula / RNDC (logística)
