"""
Blockchain simple basada en SHA-256 para registrar de forma inmutable
los resultados de los algoritmos de detección de phishing (AlexNet, SiCNN,
o el modelo de texto).

Cada bloque contiene:
- índice
- timestamp
- datos (el resultado del algoritmo: métricas, o un resultado individual)
- hash del bloque anterior
- hash propio (calculado con SHA-256 sobre todo lo anterior)

Si alguien modifica los datos de un bloque después de creado, su hash ya
no coincide, y esto rompe la cadena hacia adelante — lo cual permite
detectar la alteración.
"""
import hashlib
import json
import time


class Bloque:
    def __init__(self, indice, datos, hash_anterior):
        self.indice = indice
        self.timestamp = time.time()
        self.datos = datos
        self.hash_anterior = hash_anterior
        self.hash_propio = self.calcular_hash()

    def calcular_hash(self):
        contenido = json.dumps({
            "indice": self.indice,
            "timestamp": self.timestamp,
            "datos": self.datos,
            "hash_anterior": self.hash_anterior,
        }, sort_keys=True, default=str)
        return hashlib.sha256(contenido.encode("utf-8")).hexdigest()

    def to_dict(self):
        return {
            "indice": self.indice,
            "timestamp": self.timestamp,
            "datos": self.datos,
            "hash_anterior": self.hash_anterior,
            "hash_propio": self.hash_propio,
        }


class Blockchain:
    def __init__(self):
        self.cadena = [self._crear_bloque_genesis()]

    def _crear_bloque_genesis(self):
        return Bloque(indice=0, datos={"info": "Bloque génesis"}, hash_anterior="0" * 64)

    def registrar_resultado(self, algoritmo: str, datos: dict):
        """
        Registra el resultado de un algoritmo (AlexNet, SiCNN, modelo de
        texto, etc.) como un nuevo bloque en la cadena.
        """
        ultimo_bloque = self.cadena[-1]
        nuevo_bloque = Bloque(
            indice=len(self.cadena),
            datos={"algoritmo": algoritmo, **datos},
            hash_anterior=ultimo_bloque.hash_propio,
        )
        self.cadena.append(nuevo_bloque)
        return nuevo_bloque

    def verificar_integridad(self):
        """
        Recorre toda la cadena y verifica que:
        1. El hash de cada bloque coincida con su contenido actual.
        2. El hash_anterior de cada bloque coincida con el hash_propio
           del bloque previo.
        Devuelve (es_valida, lista_de_bloques_corruptos).
        """
        bloques_corruptos = []
        for i in range(1, len(self.cadena)):
            actual = self.cadena[i]
            anterior = self.cadena[i - 1]

            if actual.calcular_hash() != actual.hash_propio:
                bloques_corruptos.append((i, "hash propio no coincide con el contenido"))
            if actual.hash_anterior != anterior.hash_propio:
                bloques_corruptos.append((i, "hash_anterior no coincide con el bloque previo"))

        return (len(bloques_corruptos) == 0, bloques_corruptos)

    def guardar_json(self, ruta: str):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.cadena], f, indent=2, ensure_ascii=False)

    @classmethod
    def cargar_json(cls, ruta: str):
        """
        Carga una blockchain previamente guardada, preservando exactamente
        los hashes y timestamps originales (no los recalcula), para que
        la cadena persista correctamente entre reinicios del servidor.
        """
        with open(ruta, "r", encoding="utf-8") as f:
            datos_bloques = json.load(f)

        instancia = cls.__new__(cls)
        instancia.cadena = []
        for d in datos_bloques:
            bloque = Bloque.__new__(Bloque)
            bloque.indice = d["indice"]
            bloque.timestamp = d["timestamp"]
            bloque.datos = d["datos"]
            bloque.hash_anterior = d["hash_anterior"]
            bloque.hash_propio = d["hash_propio"]
            instancia.cadena.append(bloque)
        return instancia

    def imprimir_cadena(self):
        for b in self.cadena:
            print(f"Bloque {b.indice} | hash: {b.hash_propio[:16]}... | datos: {b.datos}")
