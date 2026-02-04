/**
 * Gerador de Estrutura de Vocabulário Vana v6.3 Diamond
 * Este script configura a planilha mestra para o sincronizador.
 */

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔥 Forja Vana')
      .addItem('Configurar Planilha Mestra', 'setupVanaSheet')
      .addToUi();
}

function setupVanaSheet() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  sheet.setName("Vocabulário Diamond");
  
  // 1. Cabeçalhos (Exatamente como o sync_vocabulary.py espera)
  var headers = [["slug", "tag_iast", "categoria", "descricao"]];
  sheet.getRange(1, 1, 1, 4).setValues(headers);
  
  // 2. Estilização dos Cabeçalhos
  var headerRange = sheet.getRange("A1:D1");
  headerRange.setBackground("#462066") // Roxo Vana
             .setFontColor("white")
             .setFontWeight("bold")
             .setHorizontalAlignment("center");
  
  // 3. Exemplos de preenchimento (IAST Perfeito)
  var examples = [
    ["narasimha-lila", "Narasiṁha-līlā", "lila", "Passatempo de Lord Narasimhadeva"],
    ["bhakti-tattva", "Bhakti-tattva", "tattva", "A ciência do serviço devocional"],
    ["bhaktivedanta", "Bhaktivedānta", "biografia", "Título dado a Srila Prabhupada"],
    ["guru-parampara", "Guru-paramparā", "tattva", "Linhagem de sucessão discipular"]
  ];
  sheet.getRange(2, 1, examples.length, 4).setValues(examples);
  
  // 4. Formatação de Colunas
  sheet.setColumnWidth(1, 150); // slug
  sheet.setColumnWidth(2, 180); // tag_iast
  sheet.setColumnWidth(3, 100); // categoria
  sheet.setColumnWidth(4, 350); // descricao
  
  // 5. Congelar o cabeçalho
  sheet.setFrozenRows(1);
  
  // 6. Adicionar validação de dados para categorias (opcional)
  var categories = ["lila", "tattva", "biografia", "verso", "cancao", "instrucao", "historia", "geral"];
  var rule = SpreadsheetApp.newDataValidation().requireValueInList(categories).build();
  sheet.getRange("C2:C1000").setDataValidation(rule);

  SpreadsheetApp.getUi().alert("✅ Planilha Diamond configurada com sucesso!\n\nAgora vá em Arquivo > Compartilhar > Publicar na Web e escolha o formato CSV.");
}