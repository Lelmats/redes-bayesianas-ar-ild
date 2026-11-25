# =============================================================
#  Red bayesiana para fibrosis pulmonar
#  Proyecto 2 - Probabilidad y Estadística (MOCA)
#  Equipo: Max Rivera, José Gallardo, Gerardo Bustos
#
#  Cómo correrlo:   python red_bayesiana.py
#  Necesita:        pip install pandas openpyxl pgmpy networkx matplotlib scikit-learn
#
#  Pasos del programa:
#   1. Leer los datos del Excel
#   2. Reglas de dirección (flechas prohibidas y obligatorias)
#   3. Bootstrap: correr Hill-Climbing + BIC muchas veces
#   4. Red final: quedarnos con las flechas que salen seguido
#   5. Tablas de probabilidad (CPT) contando pacientes
#   6. Preguntas a la red (inferencia con Bayes)
#   7. Revisar qué tan bien predice "panal"
#   8. Dibujar la red
#   9. Preguntas propias (opcional)
# =============================================================

import os
import json
import warnings

import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, accuracy_score, recall_score, roc_auc_score
import networkx as nx
import matplotlib
matplotlib.use("Agg")              # para guardar la imagen sin abrir ventana
import matplotlib.pyplot as plt

from pgmpy.estimators import HillClimbSearch, BayesianEstimator
from pgmpy.inference import VariableElimination
try:                                # el nombre cambia según la versión de pgmpy
    from pgmpy.models import DiscreteBayesianNetwork as RedBayesiana
except ImportError:
    from pgmpy.models import BayesianNetwork as RedBayesiana
try:
    from pgmpy.estimators import ExpertKnowledge
except ImportError:
    from pgmpy.causal_discovery import ExpertKnowledge

warnings.filterwarnings("ignore")   # pgmpy avisa mucho de cosas que no nos afectan

# ---------------- Datos que se pueden cambiar ----------------
ARCHIVO = "DatosPacientesAR_B.xlsx"
REPETICIONES = 200       # veces que se repite el bootstrap
UMBRAL = 0.50            # una flecha se queda si sale en al menos 50% de las repeticiones
GUARDADO = "repeticiones_bootstrap.json"   # para no recalcular cada vez
CARPETA = os.path.dirname(os.path.abspath(__file__))


# =============================================================
# 1. LEER LOS DATOS
# =============================================================
# En el Excel: 1 = sí / presente / hombre,  2 = no / ausente / mujer
# (DiagPrevio tiene 3 opciones: 1 sí, 2 no, 3 dudoso)
# Las celdas vacías se quedan vacías y pgmpy NO las cuenta.
datos = pd.read_excel(os.path.join(CARPETA, ARCHIVO))
# Grupo_Severidad se saca del ID: si empieza con "D" es 1, si no es 2.
# (Coincide exactamente con DiagPrevio: D = DiagPrevio 1, N = DiagPrevio 2 o 3.)
datos["Grupo_Severidad"] = [1 if str(x).startswith("D") else 2 for x in datos["ID"]]
datos = datos.drop(columns=["ID"])          # el ID no es una variable clínica
datos = datos.astype("Int64").astype("category")
columnas = list(datos.columns)

print("=" * 60)
print("RED BAYESIANA - FIBROSIS PULMONAR")
print("=" * 60)
print(f"Pacientes: {len(datos)}   Variables: {len(columnas)}")
print("\nDatos vacíos por columna (no se toman en cuenta):")
for col in columnas:
    vacios = datos[col].isna().sum()
    if vacios > 0:
        print(f"   {col:16s} {vacios}")


# =============================================================
# 2. REGLAS DE DIRECCIÓN
# =============================================================
# Acomodamos las variables por niveles según el orden en el tiempo:
#   0 = demografía, 1 = exposiciones y antecedentes,
#   2 = síntomas,   3 = estudios (tomografía y biopsia)
# Regla: una flecha NO puede ir de un nivel mayor a uno menor
# (por ejemplo, un síntoma no puede causar el sexo o el tabaquismo).
NIVEL = {
    "sexo": 0,
    "Fuma": 1, "HumoL": 1, "aves": 1, "Ag aviario": 1, "DiagPrevio": 1, "TratPrevio": 1,
    "disnea": 2, "tos": 2, "dolor toracico": 2, "hemoptisis": 2, "fiebre": 2, "hipocratismo": 2,
    "DerrameP": 3, "HRTC vidrio": 3, "reticular basal": 3, "bronquiectasias": 3, "panal": 3,
    "micronodulos": 3, "mosaico": 3, "consolidacion": 3, "enfisema": 3, "BIOPSIA P": 3,
    "Grupo_Severidad": 3,
}

prohibidas = []
for a in columnas:
    for b in columnas:
        if a != b and NIVEL[a] > NIVEL[b]:
            prohibidas.append((a, b))

# Flechas que ponemos a fuerza por conocimiento médico
obligatorias = [("reticular basal", "panal"), ("bronquiectasias", "panal")]

print(f"\nFlechas prohibidas: {len(prohibidas)}   Flechas obligatorias: {len(obligatorias)}")


# =============================================================
# 3. BOOTSTRAP CON HILL-CLIMBING + BIC
# =============================================================
# En cada repetición sacamos una muestra de pacientes al azar (con
# reemplazo) y buscamos la mejor red con Hill-Climbing calificando con BIC.
def aprender_red(muestra):
    reglas = ExpertKnowledge(forbidden_edges=prohibidas, required_edges=obligatorias)
    busqueda = HillClimbSearch(muestra)
    red = busqueda.estimate(scoring_method="bic-d",   # BIC para datos discretos
                            max_indegree=3,           # máximo 3 papás por variable
                            expert_knowledge=reglas,
                            tabu_length=10,
                            max_iter=500,
                            show_progress=False)
    return list(red.edges())

ruta_guardado = os.path.join(CARPETA, GUARDADO)
if os.path.exists(ruta_guardado):
    print(f"\nUsando las repeticiones guardadas en '{GUARDADO}'")
    print("(bórralo si quieres que se vuelvan a calcular)")
    with open(ruta_guardado) as f:
        repeticiones = [[tuple(flecha) for flecha in rep] for rep in json.load(f)]
else:
    print(f"\nCorriendo {REPETICIONES} repeticiones de bootstrap (tarda unos minutos)...")
    repeticiones = []
    for i in range(REPETICIONES):
        muestra = datos.sample(n=len(datos), replace=True, random_state=i)
        repeticiones.append(aprender_red(muestra))
        if (i + 1) % 20 == 0:
            print(f"   {i + 1} de {REPETICIONES}")
    with open(ruta_guardado, "w") as f:
        json.dump(repeticiones, f)


# =============================================================
# 4. RED FINAL (CONSENSO)
# =============================================================
# fuerza     = % de repeticiones en que aparece la flecha (en cualquier sentido)
# dirección  = de esas veces, % en que apunta hacia el lado más común
conteo_par = {}       # cuántas veces aparece el par A-B
conteo_flecha = {}    # cuántas veces aparece A -> B
for rep in repeticiones:
    for a, b in rep:
        par = tuple(sorted([a, b]))
        conteo_par[par] = conteo_par.get(par, 0) + 1
        conteo_flecha[(a, b)] = conteo_flecha.get((a, b), 0) + 1

flechas = []          # (origen, destino, fuerza)
for (a, b), veces in conteo_par.items():
    ab = conteo_flecha.get((a, b), 0)
    ba = conteo_flecha.get((b, a), 0)
    origen, destino = (a, b) if ab >= ba else (b, a)
    fuerza = veces / len(repeticiones)
    direccion = max(ab, ba) / veces
    if (fuerza >= UMBRAL and direccion > 0.5) or (origen, destino) in obligatorias:
        flechas.append((origen, destino, fuerza))

flechas.sort(key=lambda x: -x[2])
grafo = nx.DiGraph([(a, b) for a, b, _ in flechas])
if not nx.is_directed_acyclic_graph(grafo):
    print("¡OJO! La red tiene un ciclo, revisar el umbral.")

print(f"\nFlechas de la red final (fuerza >= {UMBRAL:.0%}): {len(flechas)}")
for a, b, fuerza in flechas:
    print(f"   {a:16s} -> {b:16s} {fuerza:6.1%}")
sueltas = [c for c in columnas if c not in grafo.nodes()]
print(f"\nVariables sin flechas: {', '.join(sueltas)}")


# =============================================================
# 5. TABLAS DE PROBABILIDAD (CPT)
# =============================================================
# Se cuentan pacientes. Se le suma 1 a cada conteo (corrección de Laplace)
# para que ninguna probabilidad salga 0 cuando hay pocos pacientes:
#     P = (conteo + 1) / (total + número de opciones)
opciones = {c: list(datos[c].cat.categories) for c in columnas}   # ej. [1, 2]

def construir_modelo(tabla):
    modelo = RedBayesiana([(a, b) for a, b, _ in flechas])
    modelo.add_nodes_from(columnas)
    # state_names: para que conozca todas las opciones aunque en un grupo falte alguna
    estimador = BayesianEstimator(modelo, tabla, state_names=opciones)
    for cpd in estimador.get_parameters(prior_type="dirichlet", pseudo_counts=1):
        modelo.add_cpds(cpd)
    return modelo

modelo = construir_modelo(datos)
print("\nTabla de probabilidad de 'panal' dados sus papás:")
print(modelo.get_cpds("panal"))


# =============================================================
# 6. PREGUNTAS A LA RED
# =============================================================
motor = VariableElimination(modelo)

def prob_si(variable, evidencia):
    """P(variable = 1 | evidencia). Evidencia: {"tos": 1, "Fuma": 2, ...}"""
    resultado = motor.query([variable], evidence=evidencia, show_progress=False)
    posicion = resultado.state_names[variable].index(1)
    return float(resultado.values[posicion])

base = prob_si("panal", {})
print(f"\nP(panal = sí) sin saber nada del paciente: {base:.1%}")

preguntas = [
    ("Con reticular basal y bronquiectasias", {"reticular basal": 1, "bronquiectasias": 1}),
    ("Sin reticular basal ni bronquiectasias", {"reticular basal": 2, "bronquiectasias": 2}),
    ("Fumador", {"Fuma": 1}),
    ("Fumador con humo de leña y antígeno aviario", {"Fuma": 1, "HumoL": 1, "Ag aviario": 1}),
]
print("\nPreguntas de ejemplo:")
for texto, evidencia in preguntas:
    p = prob_si("panal", evidencia)
    print(f"   {texto:45s} P(panal) = {p:6.1%}   (vs base: {p / base:.2f} veces)")
print("Nota: si una variable no está conectada con 'panal' en la red,")
print("saberla no cambia la probabilidad (sale igual a la base).")


# =============================================================
# 7. ¿QUÉ TAN BIEN PREDICE LA RED?
# =============================================================
# Validación cruzada de 10 grupos (estratificada: cada grupo tiene la misma
# proporción de sí/no). Se arman las tablas con 9 grupos y se predice
# el grupo que quedó fuera. Si P(sí) >= 0.5 decimos "sí".
# (La forma de la red se aprendió con todos los datos; solo las tablas
#  se vuelven a calcular en cada grupo.)
def validar(objetivo):
    con_dato = datos[datos[objetivo].notna()]
    real = [1 if v == 1 else 0 for v in con_dato[objetivo]]       # 1 = sí
    probabilidad = [0.0] * len(con_dato)

    grupos = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    for entrenamiento, prueba in grupos.split(con_dato, real):
        tablas = pd.concat([con_dato.iloc[entrenamiento], datos[datos[objetivo].isna()]])
        motor_grupo = VariableElimination(construir_modelo(tablas))
        for i in prueba:
            fila = con_dato.iloc[i]
            evidencia = {c: int(fila[c]) for c in columnas if c != objetivo and pd.notna(fila[c])}
            r = motor_grupo.query([objetivo], evidence=evidencia, show_progress=False)
            probabilidad[i] = float(r.values[r.state_names[objetivo].index(1)])

    prediccion = [1 if p >= 0.5 else 0 for p in probabilidad]
    VN, FP, FN, VP = confusion_matrix(real, prediccion).ravel()

    print(f"\nValidación cruzada para '{objetivo}' ({len(real)} pacientes con dato):")
    print(f"   Matriz de confusión:  VP={VP}  FP={FP}  VN={VN}  FN={FN}")
    print(f"   Exactitud      = {accuracy_score(real, prediccion):.1%}")
    print(f"   Sensibilidad   = {recall_score(real, prediccion):.1%}   (de los que son 'sí', cuántos detecta)")
    print(f"   Especificidad  = {VN / (VN + FP):.1%}   (de los que son 'no', cuántos acierta)")
    print(f"   AUC            = {roc_auc_score(real, probabilidad):.3f}   (0.5 = adivinar al azar, 1 = perfecto)")

validar("panal")
validar("Grupo_Severidad")
print("   Ojo: Grupo_Severidad coincide 100% con DiagPrevio, por eso sale perfecto o casi.")


# =============================================================
# 8. DIBUJAR LA RED
# =============================================================
# Cada nivel va en un renglón: demografía arriba, estudios abajo.
colores = {0: "#9b59b6", 1: "#3498db", 2: "#e67e22", 3: "#e74c3c"}
nombres_nivel = {0: "Demografía", 1: "Exposiciones y antecedentes",
                 2: "Síntomas", 3: "Tomografía y biopsia"}
# orden de izquierda a derecha en cada renglón (para que se crucen menos flechas)
ORDEN = ["sexo",
         "HumoL", "Fuma", "Ag aviario", "aves", "TratPrevio", "DiagPrevio",
         "tos", "hemoptisis", "dolor toracico", "hipocratismo", "disnea", "fiebre",
         "mosaico", "enfisema", "BIOPSIA P", "DerrameP", "HRTC vidrio", "reticular basal",
         "panal", "bronquiectasias", "micronodulos", "consolidacion", "Grupo_Severidad"]
posiciones = {}
for nivel in range(4):
    del_nivel = [n for n in ORDEN if n in grafo.nodes() and NIVEL[n] == nivel]
    for j, n in enumerate(del_nivel):
        x = j - (len(del_nivel) - 1) / 2
        y = -nivel * 2 + (0.7 if j % 2 else 0)       # zigzag para que no se encimen
        posiciones[n] = (x * 2.4, y)

plt.figure(figsize=(16, 9))
TAM = 900   # tamaño de los círculos
# flechas: más gruesas mientras más fuerza tenga la flecha en el bootstrap
fuerza = {(a, b): f for a, b, f in flechas}
nx.draw_networkx_edges(grafo, posiciones, arrows=True, arrowsize=16, node_size=TAM,
                       width=[1 + 2.5 * fuerza[e] for e in grafo.edges()],
                       edge_color="#666666", connectionstyle="arc3,rad=0.1")
# nodos: un círculo por variable, del color de su nivel
nx.draw_networkx_nodes(grafo, posiciones, node_size=TAM,
                       node_color=[colores[NIVEL[n]] for n in grafo.nodes()],
                       edgecolors="#333333", linewidths=1.2)
# nombres debajo de cada círculo para que se lean completos
abajo = {n: (x, y - 0.38) for n, (x, y) in posiciones.items()}
nx.draw_networkx_labels(grafo, abajo, font_size=9, font_weight="bold")
for nivel, color in colores.items():
    if any(NIVEL[n] == nivel for n in grafo.nodes()):
        plt.scatter([], [], color=color, s=120, label=nombres_nivel[nivel])
plt.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, frameon=False)
plt.title(f"Red bayesiana final ({len(flechas)} flechas, {REPETICIONES} repeticiones, umbral {UMBRAL:.0%})")
plt.axis("off")
plt.tight_layout()
plt.savefig(os.path.join(CARPETA, "red_final.png"), dpi=200)
print("\nDibujo guardado en 'red_final.png'")


# =============================================================
# 9. PREGUNTAS PROPIAS (OPCIONAL)
# =============================================================
print("\n" + "=" * 60)
print("Puedes preguntar la probabilidad de 'panal' para un paciente.")
print("Escribe variable=valor separados por coma. Ejemplo:")
print("   tos=1, reticular basal=1")
print("(1 = sí, 2 = no). Deja vacío y da Enter para salir.")
print("=" * 60)
while True:
    try:
        texto = input("\nPaciente: ").strip()
    except EOFError:            # por si se corre sin teclado
        break
    if texto == "":
        break
    evidencia = {}
    for parte in texto.split(","):
        if "=" in parte:
            nombre, valor = parte.split("=")
            nombre = nombre.strip()
            if nombre in columnas:
                evidencia[nombre] = int(valor)
            else:
                print(f"   No conozco la variable '{nombre}'")
    try:
        p = prob_si("panal", evidencia)
        print(f"   P(panal = sí) = {p:.1%}   (base: {base:.1%})")
    except Exception:
        print("   No se pudo calcular: revisa que los valores sean 1 o 2.")
