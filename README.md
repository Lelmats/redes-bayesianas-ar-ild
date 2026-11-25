# Redes bayesianas para AR-ILD

Red bayesiana hecha con datos de 75 pacientes con **AR-ILD**
(Artritis Reumatoide con Enfermedad Pulmonar Intersticial).
La red busca qué variables clínicas se relacionan entre sí y calcula
probabilidades, por ejemplo la de tener **panal de abejas** en la tomografía.

Proyecto 2 de **Probabilidad y Estadística**, Maestría en Optimización y
Cómputo Aplicado (MOCA), FCAeI - UAEM.

**Equipo:** Max Rivera, José Gallardo, Gerardo Bustos.

---

## Archivos

| Archivo | Qué es |
|---|---|
| `red_bayesiana.py` | El programa (todo está aquí) |
| `DatosPacientesAR_B.xlsx` | Los datos: 75 pacientes y 23 variables (1 = sí, 2 = no) |
| `repeticiones_bootstrap.json` | Las 200 repeticiones ya calculadas, para que corra rápido |
| `red_final.png` | Dibujo de la red final |

## Cómo usarlo

1. Instalar las librerías (solo la primera vez):

   ```
   pip install pandas openpyxl pgmpy networkx matplotlib scikit-learn
   ```

2. Correr el programa:

   ```
   python red_bayesiana.py
   ```

   Tarda unos segundos porque usa `repeticiones_bootstrap.json`.
   Si se borra ese archivo, se recalculan las 200 repeticiones (unos 4 minutos).

3. Al final se pueden hacer preguntas sobre un paciente:

   ```
   Paciente: reticular basal=1, bronquiectasias=1
      P(panal = sí) = 47.8%   (base: 45.3%)
   ```

   Se usan los nombres de las columnas del Excel, con 1 = sí y 2 = no.
   Enter vacío para salir.

## Qué hace el programa

1. **Lee el Excel.** Las celdas vacías no se cuentan.
2. **Reglas de dirección.** Las variables van en 4 niveles: demografía,
   exposiciones y antecedentes, síntomas, y tomografía/biopsia. Una flecha
   no puede ir de un nivel mayor a uno menor. Además se ponen a fuerza
   2 flechas: `reticular basal → panal` y `bronquiectasias → panal`.
3. **Bootstrap.** 200 veces se toma una muestra al azar de pacientes y se
   busca la mejor red con **Hill-Climbing**, calificando con **BIC**.
4. **Red final.** Se quedan las flechas que salieron en al menos el 50% de
   las repeticiones (23 flechas).
5. **Tablas de probabilidad (CPT).** Se cuentan pacientes y se suma 1 a
   cada conteo (corrección de Laplace) para que nada salga 0:
   `P = (conteo + 1) / (total + opciones)`.
6. **Preguntas.** Probabilidad de panal según lo que se sabe del paciente.
7. **Validación cruzada.** 10 grupos estratificados; se mide exactitud,
   sensibilidad, especificidad y AUC con scikit-learn.
8. **Dibujo.** Guarda `red_final.png`.

## Resultados principales

| | Resultado |
|---|---|
| Flechas en la red final | 23 (19 variables conectadas, 5 sueltas) |
| Probabilidad base de panal | 45.3% |
| Con reticular basal y bronquiectasias | 47.8% |
| Sin reticular basal ni bronquiectasias | 22.2% |
| AUC para panal | 0.44 (no predice mejor que el azar) |

**Lo que se encontró:**
- La red encuentra relaciones fuertes entre las exposiciones: el antígeno
  aviario se conecta con aves, humo de leña, tratamiento previo y varios
  síntomas.
- Saber si el paciente fuma, usa leña o tiene aves **no cambia** la
  probabilidad de panal: esas variables no están conectadas con panal
  por un camino abierto en la red.
- Lo único que mueve la probabilidad de panal es no tener reticular basal
  ni bronquiectasias, y en ese caso baja a la mitad.
- Con 75 pacientes la red **no logra predecir panal** (AUC menor que 0.5).

## Cosas a tomar en cuenta

- **Grupo_Severidad** se saca del ID del paciente (D = 1, N = 2) y coincide
  al 100% con `DiagPrevio`. Por eso su validación sale perfecta: no es una
  predicción real.
- `disnea` y `tos` casi no varían: solo 1 paciente dice "no".
- `DiagPrevio` tiene 3 opciones (1 sí, 2 no, 3 dudoso).
- Hay muchos datos vacíos en las variables de tomografía (por ejemplo,
  enfisema solo tiene 54 de 75).
- 75 pacientes son pocos para 23 variables; los resultados son para
  practicar el método, no para usarse con pacientes reales.

## Comprobación a mano

De los pacientes con `reticular basal = 1` y `bronquiectasias = 1`,
21 tienen dato de panal y 10 tienen panal = 1:

```
P(panal = 1) = (10 + 1) / (21 + 2) = 11/23 = 0.478
```

Es lo mismo que da el programa (47.8%).
