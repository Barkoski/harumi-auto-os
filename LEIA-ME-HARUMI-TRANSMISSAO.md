# Atualização proposta — Subaru Impreza SW 1993, EJ18, câmbio manual AWD

Base consultada: árvore principal `6bd67be13115c89d3cabb0e2f0d69f910ec9e11a`, obtida em 27/11/2026. Esta revisão foi preparada a partir dessa versão do repositório. As validações descritas abaixo se referem ao ambiente de preparação.

## O que muda

- A resposta de identificação descreve a caixa manual AWD de cinco marchas doadora de 1994, conforme informação de Lucas. As perguntas de óleo, sintomas, luz do câmbio e códigos não devem receber respostas específicas do 4EAT como diagnóstico atual.
- As entradas antigas e a tabela antiga de códigos foram preservadas em `docs/subaru/HISTORICO-4EAT.json`, sem integração à consulta ativa. São dados históricos não revalidados, não instruções de serviço.
- A base Linux é exportada do Java por `python linux/tools/export_car_knowledge.py`; o código Linux também bloqueia a interpretação de códigos da TCU como códigos da caixa atual.
- Respostas novas para diferencial, embreagem e guincho; valores não confirmados foram retirados. As respostas antigas de velas, correia, scanner e motor foram tornadas mais cautelosas.

## Fontes e limites mecânicos

- [Manual de serviço Subaru Impreza 1994, seção 2-10, páginas impressas 3–4](https://project-car.net/wp-content/uploads/2020/03/1994-impreza-service-manuals.pdf): a versão de acionamento mecânico possui cabo e o procedimento menciona folga na alavanca de 3–4 mm. O mesmo manual trata também de outras configurações. **Não confirmei qual acionamento está instalado no carro convertido**, portanto o valor não foi apresentado como regulagem aplicável.
- [Manual suplementar Subaru Impreza 1994](https://www.manualslib.com/manual/1101774/Subaru-1994-Impreza.html): contém seções de óleo de transmissão/diferenciais e da transmissão manual. Sua existência não comprova que cada especificação se aplica ao conjunto instalado.
- [Catálogo de lubrificantes AMSOIL para Impreza EJ18 1994](https://www.amsoil.com/lookup/auto-and-light-truck/1994/subaru/impreza/1-8l-4-cyl-engine-code-2-ej18s-x/): indica 75W-90 API GL-5 para certas caixas AWD TM702 e TY752; é fonte comercial e apresenta capacidades repetidas e diferentes. Não identifica com segurança a caixa instalada nem resolve sua capacidade. Use esses dados como referência de pesquisa, não como autorização para abastecer.
- [Manual de serviço Subaru Impreza 1994, seção 2-10](https://project-car.net/wp-content/uploads/2020/03/1994-impreza-service-manuals.pdf): inspeção do mecanismo de acionamento da embreagem; peças e regulagem dependem do conjunto instalado.

É necessário confirmar código completo estampado da caixa, mercado/versão, diferencial traseiro, relação final de ambos os eixos, eventual LSD, acionamento efetivamente montado, volante/embreagem e ECU/chicote após o swap. O código TY752VY3BA aparece em histórico anterior, mas não foi comprovado nesta inspeção como sendo o da caixa efetivamente instalada. Sem identificação confirmada, não definir quantidade de óleo, torques, relações, número de peça, intervalos específicos ou códigos da caixa.

## Verificações antes de uso

1. Confira o estado da instalação no veículo e preserve alterações locais antes de atualizar.
2. Regenere a base Linux com `python linux/tools/export_car_knowledge.py` e verifique se o JSON resultante permanece igual ao entregue.
3. Foram alterados identificadores de respostas para evitar reaproveitar gravações antigas com o mesmo ID. Gere os arquivos de voz e o manifesto correspondentes com `scripts/prepare_voice_cache.py` de acordo com as dependências e instruções do projeto. **Os novos áudios do cache não foram gerados nesta revisão**. O teste de cache permite a ausência temporária dos IDs revisados, que devem usar síntese quando não houver texto idêntico no manifesto. Verifique também a reprodução real e o comportamento de fallback em aparelho; não se presume que a mudança de ID por si só garanta reprodução segura.
4. Execute a suíte completa Android/Gradle, os testes Linux e um teste real de voz; valide se outros prompts, caches, documentação ou respostas geradas pelo modelo contêm instruções antigas. Este pacote não foi testado no veículo, em Android ou no fluxo completo do aplicativo. Não é garantia contra respostas incorretas do modelo local fora das frases cobertas.

## Testes

Executado: `python -m unittest discover -s tests -p 'test_*.py' -v` — passou, com nove perguntas reais e verificação da tabela automática vazia. `python -m py_compile` passou nos arquivos Python. O teste `tests/KnowledgeRegression.java` foi preparado, mas não executado: `javac` indisponível. O teste JUnit existente foi ajustado para os novos IDs, mas a suíte Android não foi executada, e seu teste de cache de voz continuará pendente até a geração dos novos arquivos.
