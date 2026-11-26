# Redes bayesianas para AR-ILD

Proyecto 2 de **Probabilidad y Estadística**, Maestría en Optimización y Cómputo
Aplicado (MOCA), FCAeI - UAEM. Dra. Elizabeth Santiago.

**Equipo:** Max Rivera, José Gallardo, Gerardo Bustos.

**En una línea:** con los datos de 75 pacientes armamos una red que muestra qué
variables clínicas se relacionan entre sí y calcula la probabilidad de daño
pulmonar avanzado (panal) según lo que se sabe del paciente.

**AR-ILD** = Enfermedad Pulmonar Intersticial asociada a Artritis Reumatoide.
**Panal** (panal de abejas) = fibrosis avanzada e irreversible que se ve en la
tomografía.

---

## Archivos

| Archivo | Qué es |
|---|---|
| `red_bayesiana.py` | El programa (todo está aquí) |
| `DatosPacientesAR_B.xlsx` | Datos: 75 pacientes, 23 variables (1 = sí, 2 = no) |
| `repeticiones_bootstrap.json` | Las 200 repeticiones ya calculadas (para que corra rápido) |
| `asociaciones.csv` | Asociación de cada par de columnas (análisis aparte, no lo genera el programa) |
| `red_final.png` | Dibujo de la red final |

## Cómo usarlo

```
pip install pandas openpyxl pgmpy networkx matplotlib scikit-learn
python red_bayesiana.py
```

- Tarda unos segundos porque usa `repeticiones_bootstrap.json`. Si se borra,
  recalcula las 200 repeticiones (unos 4 minutos).
- Al final se pueden hacer preguntas: `reticular basal=1, bronquiectasias=1`
  (1 = sí, 2 = no, nombres igual que en el Excel). Enter vacío para salir.
- En Windows con Anaconda, correrlo desde la terminal con `python`, no con el
  botón ▶ de VS Code (puede usar otro Python sin las librerías).

---

## Los datos

| Dato | Valor |
|---|---|
| Pacientes | 75 (47 con ID "D", 28 con ID "N") |
| Variables | 23 clínicas + Grupo_Severidad (la crea el código) |
| Codificación | 1 = sí / hombre, 2 = no / mujer. DiagPrevio: 1 sí, 2 no, 3 dudoso |
| Pacientes con todo completo | 38 de 75 |
| Más vacíos | enfisema (21), consolidación (16), reticular y vidrio (15), panal (13) |

**Cosas importantes que notamos:**

- **Grupo_Severidad es copia de DiagPrevio.** Se crea con la letra del ID
  (D = 1, N = 2), y los 47 "D" tienen DiagPrevio = 1 y los 28 "N" tienen 2 o 3.
  Por eso la red la "predice" casi perfecto: no es un logro.
- **TratPrevio casi separa D de N:** 91% de los D tuvieron tratamiento, 0% de
  los N. Sin DiagPrevio la red todavía separa D/N (AUC 0.925), pero por el
  historial, no por el pulmón.
- **En lo clínico D y N casi no difieren.** Solo tabaquismo (23% D contra 46% N,
  p = 0.045). Panal 54% contra 30%, pero no significativo (p = 0.11).
- **Disnea y tos casi no varían** (74/75 y 73/74 dicen sí): no ayudan a
  distinguir pacientes.

## Datos incompletos (no se imputa)

- **No imputamos** (no inventamos valores): un estudio que no se hizo no es un
  resultado negativo.
- **No borramos** a los incompletos: solo quedarían 38 de 75.
- **En cada cálculo contamos solo a los pacientes que tienen ese dato.**
  Ejemplo: la tabla de panal usa a los que tienen panal, reticular y
  bronquiectasias registrados; un paciente sin tomografía no entra ahí, pero sí
  en las tablas de tabaquismo y síntomas.
- No se usó EM.

---

## Método (paso a paso)

1. **Leer datos.** Celdas vacías se quedan vacías.
2. **Reglas de dirección.** 4 niveles por orden en el tiempo: demografía →
   exposiciones → síntomas → estudios. Una flecha no puede ir "hacia atrás"
   (191 prohibidas). Dos obligatorias, tomadas de la literatura (Chai et al.
   2023, Laria et al. 2022): reticular basal → panal y bronquiectasias → panal.
3. **Buscar la red (Hill-Climbing + BIC).**
   - **BIC** = la calificación: premia explicar bien los datos y castiga cada
     flecha extra.
   - **Hill-Climbing** = la búsqueda: empieza sin flechas, prueba agregar,
     quitar o voltear una, y se queda con el cambio que más sube la
     calificación, hasta que nada mejora. Máximo 3 papás, lista tabú de 10.
4. **Bootstrap y red final.** Se repite 200 veces con 75 pacientes al azar
   (con reemplazo) y se quedan las flechas que salen en al menos 50% de las
   veces. Con 85% la red se partía en dos.
5. **Tablas de probabilidad.** Contar pacientes y sumar 1 a cada conteo
   (Laplace) para que nada salga 0: P = (conteo + 1) / (total + opciones).
6. **Preguntas a la red.** P(panal | lo que se sabe), con eliminación de
   variables (teorema de Bayes).
7. **Validación cruzada.** 10 grupos estratificados: aprende con 9, predice el
   que quedó fuera. Exactitud, sensibilidad, especificidad y AUC.
8. **Dibujo.** Grafo con círculos por nivel; flechas más gruesas = más fuerza.
9. **Preguntas propias** (opcional).

**Modelo:** red bayesiana discreta multiconectada (no es Naive Bayes: no está
centrada en una sola variable).

**Librerías:** pgmpy (red, BIC, tablas, inferencia), pandas (datos),
scikit-learn (validación), networkx y matplotlib (dibujo).

**Markov en el proyecto:**
- *Condición de Markov:* cada variable depende solo de sus papás; por eso bastan
  56 probabilidades en lugar de 25 millones.
- *Cobija de Markov de panal:* reticular basal y bronquiectasias.
- *Equivalencia de Markov:* A → B y B → A pueden dar el mismo BIC; por eso se
  necesitan las reglas de dirección.

---

## Resultados

**Asociación entre columnas** (análisis aparte, no está en el programa): para
cada par de columnas se hizo una tabla 2×2 con prueba exacta de Fisher (p),
odds ratio (OR), V de Cramér y corrección por muchas pruebas (q). De 244 pares
revisados, 12 tienen p < 0.05 y solo 2 siguen significativos con la corrección
(q < 0.05):

| Par | OR | p | Lectura |
|---|---|---|---|
| DiagPrevio – TratPrevio | ∞ | < 0.0001 | Los diagnosticados son los tratados |
| sexo – Fuma | 11.4 | 0.0003 | Los hombres fuman mucho más |
| Fuma – HumoL | 0.19 | 0.003 | Quien fuma suele no tener humo de leña |
| TratPrevio – panal | 4.9 | 0.008 | Los tratados tienen más panal |
| aves – hipocratismo | 4.1 | 0.019 | |
| panal – Ag aviario | 0.16 | 0.026 | Antígeno aviario positivo, menos panal |

(La lista completa está en `asociaciones.csv`.)

**Red final:** 23 flechas, 19 variables conectadas.

- Eje de exposiciones: antígeno aviario conectado con aves, humo de leña,
  tabaco, tratamiento previo y síntomas.
- Eje de tomografía: enfisema → biopsia → reticular, bronquiectasias, vidrio y
  derrame → panal.
- Solo los une el derrame pleural, que es un **colisionador**: mientras no se
  observe, bloquea el paso (d-separación).
- Sin flechas: sexo, disnea, fiebre, micronódulos, consolidación.

**Probabilidad de panal:**

| Lo que se sabe | P(panal) |
|---|---|
| Nada (base) | 45% |
| Reticular y bronquiectasias | 47.8% (= 11/23) |
| Ni reticular ni bronquiectasias | 22% |
| Fuma, leña o aves | 45% (no cambia) |

**Validación cruzada:**

| Objetivo | AUC | Exactitud |
|---|---|---|
| panal | 0.44 | 50% |
| Grupo_Severidad | 1.00 | 100% (porque es copia de DiagPrevio) |

AUC 0.5 = adivinar. **La red no predice panal.**

---

## ⚠️ Hallazgo importante: datos vacíos y BIC

Al comparar la asociación entre columnas con la red, **solo 2 de las 23 flechas tienen asociación
par a par** (DiagPrevio – TratPrevio y Fuma – HumoL). Varias flechas fuertes de
la red no tienen asociación en los datos. Por ejemplo, Ag aviario → tos: entre
los pacientes con antígeno registrado, **todos** tienen tos, así que no puede
haber asociación.

**Por qué pasa:** el BIC cuenta solo a los pacientes con dato en la variable y
en sus papás. Si se agrega un papá con muchos vacíos, se usan **menos
pacientes**, y la calificación "mejora" solo por eso.

| Tabla | Sin papá | Con papá | Pacientes usados |
|---|---|---|---|
| tos | −7.5 | −4.3 con Ag aviario | 74 → 62 |
| aves | −54.0 | −45.3 con Ag aviario | 75 → 63 |
| BIOPSIA P | −40.0 | −34.5 con enfisema | 61 → 49 |

Por eso las variables con más vacíos (Ag aviario con 12, enfisema con 21,
biopsia con 14) terminan como "papás" de muchas otras. **Parte de la estructura
de la red se debe a los datos vacíos, no a relaciones reales.**

Opciones para corregirlo (pendiente de decidir en equipo):

1. Aprender la red solo con los 38 pacientes completos.
2. Tratar el vacío como una tercera opción ("no evaluado").
3. Reportarlo como limitación y apoyarse en la asociación entre columnas.

---

## Lo que no se usó

Chi-cuadrada como filtro previo, regresión logística bayesiana con PMP,
regresión Beta e índices (artículo de Reveco-Quiroz), EM e imputación.
Estaban en el plan del 17 de noviembre; con datos dicotómicos se cambió a
aprendizaje de estructura con BIC.

## Limitaciones

- 75 pacientes para 23 variables (N/p ≈ 3.3).
- Solo 38 pacientes completos, y los vacíos afectan al BIC (ver arriba).
- Disnea y tos casi constantes.
- Grupo_Severidad es copia de DiagPrevio.
- La estructura se aprende con todos los datos antes de la validación.
- Las flechas son asociaciones, no causas. Las reglas de dirección no las
  revisó un médico.

## Comprobación a mano

De los pacientes con `reticular basal = 1` y `bronquiectasias = 1`, 21 tienen
dato de panal y 10 tienen panal = 1:

```
P(panal = 1) = (10 + 1) / (21 + 2) = 11/23 = 0.478
```

Es lo mismo que da el programa (47.8%).
