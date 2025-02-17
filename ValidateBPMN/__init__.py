import logging
import azure.functions as func
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
import json

# Cargar el modelo SentenceTransformer (esto puede tardar la primera vez)
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def vectorizar_texto(texto):
    vector = model.encode(texto)
    return vector.tolist()  # Convertir a lista para serializar a JSON

def buscar_normas_relevantes(vector_elemento, normas):
    similitudes = [cosine_similarity([vector_elemento], [norma["vector"]])[0][0] for norma in normas]
    indice_maximo = similitudes.index(max(similitudes))
    return normas[indice_maximo]

def evaluar_cumplimiento(elemento, norma):
    if "proteccion" in elemento["descripcion"].lower() and "proteccion" in norma["texto"].lower():
        return True
    else:
        return False

def ValidateBPMN(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
             "Please pass a JSON payload in the request body",
             status_code=400
        )

    if req_body and 'bpmn_element' in req_body:
        bpmn_element = req_body['bpmn_element']

        # Ejemplo de normas (esto eventualmente vendrá de Cosmos DB)
        normas = [
            {"id": "norma1", "texto": "Esta norma se refiere a la protección de datos personales.", "vector": vectorizar_texto("protección de datos personales")},
            {"id": "norma2", "texto": "Esta norma se refiere a la seguridad de la información.", "vector": vectorizar_texto("seguridad de la información")}
        ]

        # Vectorizar el elemento BPMN
        vector_bpmn = vectorizar_texto(bpmn_element["descripcion"])

        # Buscar la norma más relevante
        norma_relevante = buscar_normas_relevantes(vector_bpmn, normas)

        # Evaluar el cumplimiento
        cumple = evaluar_cumplimiento(bpmn_element, norma_relevante)

        # Crear el reporte
        reporte = {
            "elemento": bpmn_element["id"],
            "norma": norma_relevante["id"],
            "cumple": cumple
        }

        return func.HttpResponse(
            json.dumps(reporte, indent=4),
            mimetype="application/json",
            status_code=200
        )
    else:
        return func.HttpResponse(
             "Please pass a bpmn_element in the request body",
             status_code=400
        )

# La siguiente línea es crucial para el entrypoint de Azure Functions
main = ValidateBPMN

if __name__ == "__main__":
    # Esto es solo para pruebas locales
    elemento_bpmn = {"id": "tarea1", "descripcion": "Esta tarea implica el procesamiento de datos personales."}
    # Simula un request HTTP
    class MockHttpRequest:
        def get_json(self):
            return {"bpmn_element": elemento_bpmn}
    req = MockHttpRequest()
    response = ValidateBPMN(req)
    print(response.get_body().decode())
