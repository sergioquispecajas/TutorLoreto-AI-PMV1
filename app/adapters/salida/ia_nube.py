"""Adaptador opcional de IA en la nube compatible con Chat Completions."""
import os
import httpx

from app.domain.errores_ia import IANoDisponible, IATiempoAgotado, IARespuestaInvalida


class TutorNube:
    def __init__(self):
        self.api_key = os.getenv("TUTOR_ONLINE_API_KEY", "").strip()
        self.base_url = os.getenv("TUTOR_ONLINE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.modelo = os.getenv("TUTOR_ONLINE_MODEL", "gpt-4o-mini").strip()

    def estado(self) -> dict:
        return {"disponible": bool(self.api_key), "modelo": self.modelo if self.api_key else None,
                "detalle": "Tutor en línea configurado." if self.api_key else
                "El tutor en línea requiere configurar TUTOR_ONLINE_API_KEY en el servidor."}

    def responder(self, mensaje: str, asignatura: str, grado: int,
                  historial: list[dict] | None = None) -> str:
        if not self.api_key:
            raise IANoDisponible("El tutor en línea todavía no está configurado en el servidor.")
        if not self.base_url.startswith("https://") and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            raise IANoDisponible("La dirección del proveedor de IA en línea debe usar HTTPS.")
        system = (
            "Eres TutorLoreto AI, un tutor educativo amable para estudiantes de secundaria de Loreto, Perú. "
            "Responde en español claro, con lenguaje apropiado para la edad. Explica paso a paso, define términos, "
            "incluye un ejemplo sencillo y termina con una pregunta breve para comprobar comprensión cuando sea útil. "
            "No inventes fuentes, no afirmes que eres docente y reconoce cuando no sabes. "
            "No solicites nombres completos, DNI, direcciones ni datos personales. "
            f"Contexto académico: grado {grado} de secundaria; asignatura: {asignatura}."
        )
        messages = [{"role": "system", "content": system}]
        for item in (historial or [])[-8:]:
            role = item.get("role")
            content = str(item.get("content", ""))[:2500]
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": mensaje[:4000]})
        try:
            with httpx.Client(timeout=httpx.Timeout(45.0, connect=10.0), trust_env=True) as client:
                response = client.post(
                    self.base_url + "/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.modelo, "messages": messages, "temperature": 0.4, "max_tokens": 900},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.TimeoutException as exc:
            raise IATiempoAgotado("El tutor en línea tardó demasiado. Intenta nuevamente.") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise IANoDisponible("El proveedor rechazó la clave del tutor en línea. Revisa su configuración.") from exc
            if exc.response.status_code == 429:
                raise IANoDisponible("El servicio de IA en línea alcanzó su límite temporal. Intenta más tarde.") from exc
            raise IANoDisponible(f"El proveedor de IA respondió con HTTP {exc.response.status_code}.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise IANoDisponible("No se pudo conectar con el proveedor de IA en línea.") from exc
        try:
            answer = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise IARespuestaInvalida("El proveedor no devolvió una respuesta que podamos mostrar.") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise IARespuestaInvalida("El tutor en línea devolvió una respuesta vacía.")
        return answer.strip()
