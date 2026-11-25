# Red bayesiana - Fibrosis pulmonar

Proyecto 2 de Probabilidad y Estadística (MOCA).
Equipo: Max Rivera, José Gallardo, Gerardo Bustos.

## Qué hay en la carpeta

| Archivo | Qué es |
|---|---|
| `red_bayesiana.py` | El programa (todo está aquí) |
| `DatosPacientesAR_B.xlsx` | Los datos: 75 pacientes, 1 = sí, 2 = no |
| `repeticiones_bootstrap.json` | Las 200 repeticiones ya calculadas (para que corra rápido) |
| `red_final.png` | El dibujo de la red que sale al correrlo |

## Cómo usarlo

1. Instalar las librerías (solo la primera vez):

   ```
   pip install pandas openpyxl pgmpy networkx matplotlib scikit-learn
   ```

2. Entrar a la carpeta y correr:

   ```
   python red_bayesiana.py
   ```

   Con el archivo `repeticiones_bootstrap.json` tarda unos segundos.
   Si lo borras, vuelve a calcular las 200 repeticiones (unos 4 minutos).

3. Al final pregunta por un paciente. Se escribe así:

   ```
   Paciente: reticular basal=1, bronquiectasias=1
      P(panal = sí) = 47.8%   (base: 45.3%)
   ```

   Enter vacío para salir.

## Qué hace, paso por paso

1. **Lee el Excel.** Las celdas vacías no se cuentan.
2. **Reglas de dirección.** Las variables van en 4 niveles (demografía,
   exposiciones, síntomas, estudios). Una flecha no puede ir de un nivel
   mayor a uno menor. Además se ponen a fuerza 2 flechas:
   reticular basal → panal y bronquiectasias → panal.
3. **Bootstrap.** 200 veces: se toma una muestra al azar de pacientes y se
   busca la mejor red con Hill-Climbing, calificando con BIC.
4. **Red final.** Se quedan las flechas que salieron en al menos 50% de las
   repeticiones.
5. **Tablas (CPT).** Se cuentan pacientes y se suma 1 a cada conteo
   (Laplace) para que nada salga 0:
   P = (conteo + 1) / (total + opciones).
6. **Preguntas.** Probabilidad de panal según lo que se sabe del paciente.
7. **Validación.** Se separan los pacientes en 10 grupos y se revisa
   qué tan bien predice panal (exactitud, sensibilidad, especificidad y AUC,
   calculadas con scikit-learn).
8. **Dibujo.** Guarda `red_final.png`.

## Para cambiar algo

Arriba del programa están `REPETICIONES` y `UMBRAL`. Si se cambian, hay
que borrar `repeticiones_bootstrap.json` para que se recalcule.

## Comprobación a mano

De los pacientes con reticular basal = 1 y bronquiectasias = 1,
21 tienen dato de panal y 10 tienen panal = 1:

    P(panal = 1) = (10 + 1) / (21 + 2) = 11/23 = 0.478

Es lo mismo que da el programa (47.8%).
