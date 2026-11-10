# Handyman-project

- Orçamentos e projetos ficam em `projetos-madeira/clientes/<cliente>/<projeto>/` (nomes em minúsculas, com hífens). Nunca crie arquivos de projeto soltos em `projetos-madeira/` nem na raiz do repositório.
- Ao começar um orçamento novo, pergunte o nome do cliente se ele não tiver sido informado. Crie a pasta do projeto com `referencias/`, `orcamento/`, `desenhos/` e `propostas/`, e acrescente uma linha na tabela de `projetos-madeira/README.md`.
- Skills: `.claude/skills/orcamento-madeira` (orçamento) e `.claude/skills/desenho-madeira` (desenhos). Mostre prévias (`--previa`) antes de emitir PDFs finais.
- Material de referência sem cliente vai em `projetos-madeira/referencias/`.
