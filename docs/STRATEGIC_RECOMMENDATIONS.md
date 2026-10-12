# Recomendações Estratégicas — Evolução do Panvel AI Assistant

## 1. Objetivo

Este documento apresenta recomendações para evoluir o protótipo desenvolvido no desafio técnico para uma solução corporativa de Inteligência Artificial Generativa.

As recomendações consideram qualidade das respostas, segurança farmacológica, escalabilidade, governança dos dados, custos e experiência do usuário.

As funcionalidades descritas a seguir representam propostas de evolução, não recursos necessariamente implementados no protótipo.

---

## 2. Prioridade 1 — Segurança e confiabilidade

### 2.1. Avaliação sistemática das respostas farmacológicas

**Problema**

Mesmo utilizando RAG, um modelo generativo pode interpretar incorretamente informações recuperadas ou produzir afirmações sem suporte documental suficiente.

**Recomendação**

Criar uma base de avaliação contendo perguntas e respostas revisadas por profissionais habilitados.

O conjunto deve contemplar:

- Efeitos adversos.
- Contraindicações.
- Interações medicamentosas.
- Informações sobre composição.
- Medicamentos ausentes do corpus.
- Perguntas ambíguas.
- Solicitações de orientação individual.
- Situações de risco.

**Indicadores sugeridos**

- Taxa de respostas factualmente corretas.
- Percentual de afirmações sustentadas por fontes.
- Taxa de respostas sem suporte documental.
- Taxa de recusas apropriadas.
- Taxa de respostas potencialmente inseguras.

**Benefício esperado**

Reduzir riscos e estabelecer critérios objetivos para a evolução do sistema.

---

### 2.2. Validação de citações

**Problema**

A identificação de uma bula citada não garante que todas as afirmações da resposta estejam efetivamente presentes no documento.

**Recomendação**

Evoluir o mecanismo de citações para associar afirmações a trechos específicos recuperados.

Uma possível abordagem seria apresentar:

- Nome da bula.
- Trecho utilizado.
- Identificador do chunk.
- Localização no documento, quando disponível.

**Benefício esperado**

Maior auditabilidade e facilidade de revisão das respostas.

---

### 2.3. Revisão humana em cenários críticos

**Recomendação**

Definir políticas para perguntas que envolvam maior risco, incluindo:

- Suspeitas de reações adversas graves.
- Intoxicação.
- Interações potencialmente perigosas.
- Solicitações de prescrição.
- Recomendações individualizadas.

O assistente deve possuir limites operacionais claros e encaminhar situações que exijam avaliação profissional.

**Benefício esperado**

Reduzir o risco de utilização inadequada do sistema em decisões clínicas.

---

## 3. Prioridade 2 — Governança dos documentos

### 3.1. Atualização controlada das bulas

**Problema**

Informações farmacológicas podem mudar ao longo do tempo.

**Recomendação**

Implementar um processo de atualização documental com:

1. Identificação da origem oficial.
2. Registro da versão do documento.
3. Data de atualização.
4. Validação do conteúdo extraído.
5. Reindexação controlada.
6. Histórico de alterações.

**Benefício esperado**

Reduzir a utilização de informações desatualizadas.

---

### 3.2. Versionamento do índice vetorial

**Recomendação**

Associar cada índice a uma versão identificável do corpus.

Isso permitiria:

- Reproduzir resultados.
- Investigar respostas anteriores.
- Comparar estratégias de chunking.
- Executar rollback em caso de problemas.

**Benefício esperado**

Maior controle sobre a evolução da base de conhecimento.

---

## 4. Prioridade 3 — Qualidade da recuperação RAG

### 4.1. Avaliação de estratégias de chunking

**Recomendação**

Comparar diferentes tamanhos de chunks e níveis de sobreposição.

A avaliação deve considerar:

- Preservação do contexto.
- Recuperação de informações específicas.
- Fragmentação de tabelas.
- Separação inadequada de seções.
- Custo de processamento.

**Benefício esperado**

Melhorar a qualidade do contexto enviado ao modelo.

---

### 4.2. Busca híbrida

**Recomendação**

Avaliar a combinação de busca vetorial com busca lexical.

A busca lexical pode ser especialmente útil para:

- Nomes comerciais.
- Princípios ativos.
- Termos farmacológicos específicos.
- Expressões que exigem correspondência textual exata.

**Benefício esperado**

Aumentar a precisão em consultas nas quais a similaridade semântica isolada não é suficiente.

---

### 4.3. Re-ranking

**Recomendação**

Avaliar um estágio adicional de ordenação dos documentos recuperados.

Um modelo de re-ranking poderia selecionar os trechos mais relevantes antes da geração da resposta.

**Trade-off**

A técnica pode melhorar a relevância, mas adiciona custo computacional e latência.

Sua adoção deve depender de resultados medidos.

---

## 5. Prioridade 4 — Desempenho e custos

### 5.1. Redução da latência do roteamento

**Cenário atual**

O roteamento utiliza uma chamada ao modelo de linguagem.

**Recomendação**

Avaliar uma estratégia híbrida:

- Regras determinísticas para perguntas evidentes.
- Classificação por LLM para perguntas ambíguas.

**Benefício esperado**

Redução de chamadas desnecessárias ao modelo.

---

### 5.2. Cache de consultas

**Recomendação**

Avaliar cache para operações adequadas, como:

- Consultas frequentes de filiais.
- Embeddings de perguntas repetidas.
- Resultados de recuperação documental.

O cache deve considerar atualização dos dados e invalidação.

**Benefício esperado**

Reduzir latência e consumo de recursos.

---

### 5.3. Otimização do contexto

**Recomendação**

Monitorar a quantidade de tokens enviada ao modelo.

Avaliar:

- Redução de trechos redundantes.
- Ajuste do número de chunks.
- Compactação de históricos longos.
- Seleção mais precisa do contexto.

**Benefício esperado**

Reduzir custos sem comprometer a qualidade das respostas.

---

### 5.4. Medição individual de ferramentas

**Cenário atual**

A métrica `tool_orchestration_ms` agrega diferentes operações.

**Recomendação**

Separar medições de:

- Tempo de decisão do LLM.
- Tempo de validação dos argumentos.
- Tempo de execução de cada ferramenta.
- Tempo de geração da resposta final.

**Benefício esperado**

Identificar gargalos com maior precisão.

---

## 6. Prioridade 5 — Evolução do Tool Calling

### 6.1. Integração com serviços corporativos

**Recomendação**

Em uma evolução futura, substituir ou complementar arquivos locais por APIs corporativas autorizadas.

Exemplos de possibilidades:

- Cadastro atualizado de filiais.
- Serviços disponíveis por unidade.
- Horários de funcionamento.
- Informações operacionais aprovadas para consulta.

**Benefício esperado**

Acesso a dados mais recentes, sem depender exclusivamente de arquivos estáticos.

---

### 6.2. Governança das ferramentas

**Recomendação**

Manter um catálogo de ferramentas com:

- Nome.
- Finalidade.
- Schema de entrada.
- Permissões necessárias.
- Limites de execução.
- Tratamento de erros.
- Auditoria.

**Benefício esperado**

Reduzir riscos conforme novas integrações forem adicionadas.

---

## 7. Prioridade 6 — Observabilidade em produção

### 7.1. Métricas e dashboards

**Cenário atual**

A aplicação registra logs estruturados por turno.

**Recomendação**

Integrar as métricas a uma plataforma de observabilidade.

Indicadores relevantes:

- Latência média.
- Latência p95 e p99.
- Taxa de erros.
- Consumo de tokens.
- Custo estimado por requisição.
- Frequência de execução das ferramentas.
- Taxa de consultas sem documentos relevantes.
- Distribuição de perguntas por rota.

**Benefício esperado**

Acompanhar desempenho, estabilidade e custo operacional.

---

### 7.2. Alertas

**Recomendação**

Criar alertas para situações como:

- Aumento significativo da latência.
- Falhas frequentes na API do LLM.
- Indisponibilidade do Qdrant.
- Falhas no processo de indexação.
- Aumento de respostas sem contexto suficiente.

**Benefício esperado**

Reduzir o tempo de identificação e resolução de incidentes.

---

## 8. Prioridade 7 — Segurança corporativa

### 8.1. Autenticação e autorização

**Recomendação**

Adicionar autenticação e políticas de autorização antes de disponibilizar a solução em ambientes corporativos.

O acesso às ferramentas deve respeitar as permissões de cada usuário.

---

### 8.2. Proteção de dados

**Recomendação**

Estabelecer políticas de:

- Minimização de dados pessoais.
- Tratamento de informações sensíveis.
- Retenção de históricos.
- Controle de acesso aos logs.
- Mascaramento de dados quando necessário.
- Gestão segura de credenciais.

Essas políticas devem considerar os requisitos aplicáveis da LGPD.

---

### 8.3. Proteção contra prompt injection

**Recomendação**

Avaliar mecanismos de defesa contra instruções maliciosas inseridas em perguntas ou documentos recuperados.

O conteúdo das bulas deve ser tratado como dado de referência, não como instrução com autoridade sobre o comportamento do assistente.

**Benefício esperado**

Reduzir o risco de manipulação do fluxo de execução.

---

## 9. Prioridade 8 — Escalabilidade

### 9.1. Evolução da infraestrutura

**Cenário atual**

A aplicação utiliza Docker Compose para execução local.

**Recomendação**

Para produção, avaliar:

- Serviços gerenciados.
- Orquestração de containers.
- Escalonamento horizontal.
- Balanceamento de carga.
- Gestão centralizada de segredos.
- Estratégias de backup.
- Recuperação de falhas.

A escolha deve considerar volume de acessos, disponibilidade exigida e custos.

---

### 9.2. Persistência de sessões

**Cenário atual**

O histórico conversacional é enviado pelo frontend.

**Recomendação**

Adicionar armazenamento controlado de sessões caso o produto precise oferecer:

- Continuidade entre dispositivos.
- Histórico persistente.
- Auditoria de interações.
- Gerenciamento de conversas longas.

A retenção deve respeitar políticas de privacidade.

---

## 10. Roadmap sugerido

| Fase | Prioridades | Objetivo |
|---|---|---|
| Fase 1 | Avaliação de respostas, segurança farmacológica e citações | Aumentar confiabilidade |
| Fase 2 | Governança de bulas e qualidade da recuperação | Melhorar a base documental |
| Fase 3 | Otimização de latência, tokens e ferramentas | Melhorar desempenho e custo |
| Fase 4 | Autenticação, observabilidade e integrações corporativas | Preparar operação controlada |
| Fase 5 | Escalabilidade e persistência de sessões | Suportar evolução do produto |

O roadmap é uma proposta inicial. As prioridades definitivas devem considerar requisitos de negócio, riscos e resultados de avaliações.

---

## 11. Considerações finais

O protótipo demonstra a utilização complementar de RAG e Tool Calling em um assistente conversacional.

A evolução para um produto corporativo deve priorizar segurança, qualidade das respostas e governança antes de ampliar o número de funcionalidades.

O objetivo não deve ser apenas gerar respostas em linguagem natural, mas construir um sistema confiável, auditável, sustentável e adequado às necessidades operacionais da Panvel.