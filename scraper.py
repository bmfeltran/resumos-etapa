"""
Esqueleto do scraper de videoaulas (Etapa).

Fluxo:
1. Login (ou reaproveita sessão salva)
2. Navega até a página de listagem de aulas
3. Expande accordions recursivamente (Semana -> Dia -> Materia -> Aula),
   filtrando por nome em cada nível
4. Ao clicar numa aula-folha, escuta a rede e captura a URL
   do tipo https://alunos-api.etapa.com.br/api/video/{id}/vimeo
5. Salva tudo em um JSON estruturado (lista_aulas.json)

TODO marcados no código são os pontos que dependem dos seletores
reais da página (você vai inspecionar e preencher depois).
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext

# ---------- Configuração ----------

LOGIN_URL = "https://alunos.etapa.com.br/login"  # TODO: confirmar URL
LISTAGEM_URL = "https://alunos.etapa.com.br/aulas"  # TODO: confirmar URL
SESSAO_PATH = Path("sessao.json")
SAIDA_PATH = Path("lista_aulas.json")

# Nomes que você quer filtrar, em ordem de nível da hierarquia.
# Ex.: nível 0 = Semana, nível 1 = Dia, nível 2 = Matéria.
# Deixe None num nível para "pegar todos" naquele nível.
FILTROS_POR_NIVEL = [
    None,          # Semana: todas
    None,          # Dia: todos
    "Física",      # Matéria: só Física
]

PADRAO_URL_VIMEO = "/api/video/"  # usado para reconhecer a resposta de rede


# ---------- Login / Sessão ----------

def obter_contexto(playwright, usuario: str, senha: str) -> BrowserContext:
    browser = playwright.chromium.launch(headless=True)

    if SESSAO_PATH.exists():
        context = browser.new_context(storage_state=str(SESSAO_PATH))
        return context

    context = browser.new_context()
    page = context.new_page()
    page.goto(LOGIN_URL)

    # TODO: ajustar seletores reais do formulário de login
    page.fill("#usuario", usuario)
    page.fill("#senha", senha)
    page.click("button[type=submit]")

    # TODO: trocar pelo seletor/URL que confirma login bem-sucedido
    page.wait_for_load_state("networkidle")

    context.storage_state(path=str(SESSAO_PATH))
    return context


# ---------- Captura de rede ----------

class CapturadorDeLinks:
    """Escuta respostas de rede e guarda links de vídeo junto com o breadcrumb atual."""

    def __init__(self):
        self.capturados: list[dict] = []
        self.breadcrumb: list[str] = []

    def registrar(self, page: Page):
        page.on("response", self._on_response)

    def _on_response(self, response):
        if PADRAO_URL_VIMEO in response.url:
            self.capturados.append({
                "api_url": response.url,
                "breadcrumb": list(self.breadcrumb),
            })

    def entrar_nivel(self, nome: str):
        self.breadcrumb.append(nome)

    def sair_nivel(self):
        if self.breadcrumb:
            self.breadcrumb.pop()


# ---------- Expansão recursiva dos accordions ----------

def expandir(container, nivel: int, capturador: CapturadorDeLinks, page: Page):
    """
    Expande recursivamente os accordions a partir de `container`.
    `container` pode ser a `page` inteira (nível 0) ou um locator de um
    accordion já aberto (níveis seguintes).
    """
    eh_folha = nivel >= len(FILTROS_POR_NIVEL)

    if eh_folha:
        capturar_aulas_folha(container, capturador, page)
        return

    filtro = FILTROS_POR_NIVEL[nivel]

    # TODO: ajustar seletor real do accordion e do span de nome
    accordions = container.locator("div.accordion")
    if filtro:
        accordions = accordions.filter(has=page.locator(f"span:has-text('{filtro}')"))

    total = accordions.count()
    for i in range(total):
        acc = accordions.nth(i)

        # TODO: pegar o texto real do nome pra registrar no breadcrumb
        nome = acc.locator("span").first.inner_text()

        acc.click()

        # TODO: ajustar seletor que indica "accordion aberto/carregado"
        page.wait_for_timeout(500)  # placeholder; trocar por wait_for de verdade

        capturador.entrar_nivel(nome)
        expandir(acc, nivel + 1, capturador, page)
        capturador.sair_nivel()


def capturar_aulas_folha(container, capturador: CapturadorDeLinks, page: Page):
    """
    Nível folha: os itens aqui são as aulas clicáveis que abrem o
    div externo/modal com o link do Vimeo.
    """
    # TODO: ajustar seletor real das aulas clicáveis
    aulas = container.locator(".item-aula")
    total = aulas.count()

    for i in range(total):
        aula = aulas.nth(i)

        # TODO: pegar nome real da aula
        nome_aula = aula.inner_text()
        capturador.entrar_nivel(nome_aula)

        aula.click()

        # Dá tempo pro modal/div externo abrir e disparar a chamada de rede
        # TODO: trocar por wait_for de um elemento do modal, se possível
        page.wait_for_timeout(1000)

        # TODO: fechar o modal/div externo antes de seguir pra próxima aula
        # page.locator(".fechar-modal").click()

        capturador.sair_nivel()


# ---------- Execução principal ----------

def main(usuario: str, senha: str):
    with sync_playwright() as p:
        context = obter_contexto(p, usuario, senha)
        page = context.new_page()

        capturador = CapturadorDeLinks()
        capturador.registrar(page)

        page.goto(LISTAGEM_URL)
        page.wait_for_load_state("networkidle")

        expandir(page, nivel=0, capturador=capturador, page=page)

        SAIDA_PATH.write_text(
            json.dumps(capturador.capturados, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"{len(capturador.capturados)} links capturados -> {SAIDA_PATH}")

        context.close()


if __name__ == "__main__":
    import os
    main(usuario=os.environ["ETAPA_USER"], senha=os.environ["ETAPA_PASS"])