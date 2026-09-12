# AGENTS.md

Repo de um único arquivo: `scraper.py` (skeleton do scraper de videoaulas do portal Etapa, usando Playwright). Todo o código, comentários e identificadores estão em português — mantenha a convenção em novas mudanças.

## Rodar

```sh
ETAPA_USER=<login> ETAPA_PASS=<senha> python scraper.py
```

Credenciais vêm de env vars (`ETAPA_USER`/`ETAPA_PASS`), sem argparse. Dependências: `playwright` (pip) + browser chromium (`playwright install chromium`).

## Arquivos gerados

- `sessao.json` — storage state do login, reutilizado entre execuções. Apague para forçar novo login.
- `lista_aulas.json` — saída: lista de URLs de vídeo capturadas da rede + breadcrumb.

## Gotchas

- O arquivo é um esqueleto cheio de `TODO` apontando seletores que dependem do DOM real da página. Ao implementar, substitua os `wait_for_timeout` (placeholders) por `wait_for`/`expect` reais.
- `FILTROS_POR_NIVEL` controla a hierarquia de expansão (nível 0 = Semana -> ... -> Aula); `None` = pegar tudo naquele nível. Atualmente filtra só "Física" no nível de matéria.
- Captura de URL baseia-se no padrão `/api/video/` nas respostas de rede.
- Sem git, sem testes, sem lint/config de CI.