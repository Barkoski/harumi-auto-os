package com.harumi.autoos.ai;
public class KnowledgeRegression {
 public static void main(String[] args) {
  String[][] cases={
   {"Qual óleo do câmbio manual?","óleo de engrenagens"},
   {"Quantos litros de óleo vai no câmbio?","quantidade"},
   {"O carro trepida nas curvas fechadas","AWD manual"},
   {"Qual óleo do diferencial traseiro?","diferencial traseiro"},
   {"Qual embreagem comprar?","acionamento"},
   {"código 24 do câmbio","caixa atual é manual"},
   {"Fusível FWD","histórico"},
   {"A luz AT OIL TEMP acendeu","swap manual"},
   {"Como rebocar em pane?","guincho plataforma"}
  };
  for (String[] c:cases) {String a=CarKnowledge.answer(c[0]);if(a==null || !a.toLowerCase().contains(c[1].toLowerCase()))throw new AssertionError(c[0]+" -> "+a);System.out.println(c[0]+" -> OK");}
 }
}
