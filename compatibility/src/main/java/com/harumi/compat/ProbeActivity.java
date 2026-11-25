package com.harumi.compat;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.widget.*;
import org.json.JSONObject;
import com.harumi.autoos.oem.DeviceProfileCollector;
public final class ProbeActivity extends Activity {
    private JSONObject report;
    @Override public void onCreate(Bundle state){
        super.onCreate(state);report=DeviceProfileCollector.collect(this);
        try{report.put("Diagnóstico estendido",ExtendedProbe.collect(this));}catch(Exception ignored){}
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(24,18,24,18);root.setBackgroundColor(0xff1b1b21);
        TextView title=new TextView(this);title.setText("Harumi · Compatibilidade da central");title.setTextSize(23);title.setTextColor(0xffdfacc8);root.addView(title);
        TextView note=new TextView(this);note.setText("Este app só LÊ informações da central e não altera nada. Toque em \"Compartilhar\" para enviar o relatório, ou em \"Salvar relatório\" para gravar um arquivo (ex.: no pendrive). Nada é enviado sozinho.");note.setTextSize(16);note.setTextColor(0xffd4c6d6);root.addView(note);
        ScrollView scroll=new ScrollView(this);TextView body=new TextView(this);body.setTextSize(16);body.setTextColor(0xffeee8ef);body.setPadding(0,18,0,18);
        try{body.setText(report.toString(2));}catch(Exception e){body.setText("Não foi possível formatar o relatório.");}
        scroll.addView(body);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        Button save=new Button(this);save.setText("Salvar relatório");save.setOnClickListener(v->{
            Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/json").putExtra(Intent.EXTRA_TITLE,"Harumi-central.json");
            try{startActivityForResult(intent,1);}catch(android.content.ActivityNotFoundException e){Toast.makeText(this,"Seletor de arquivos não disponível.",Toast.LENGTH_LONG).show();}
        });
        Button share=new Button(this);share.setText("Compartilhar");share.setOnClickListener(v->{
            try{
                Intent send=new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_SUBJECT,"Harumi-central").putExtra(Intent.EXTRA_TEXT,report.toString(2));
                startActivity(Intent.createChooser(send,"Enviar relatório"));
            }catch(android.content.ActivityNotFoundException e){Toast.makeText(this,"Nenhum app para compartilhar. Use Salvar relatório.",Toast.LENGTH_LONG).show();}
            catch(Exception e){Toast.makeText(this,"Não foi possível compartilhar. Use Salvar relatório.",Toast.LENGTH_LONG).show();}
        });
        for(Button b:new Button[]{share,save}){b.setTextSize(22);b.setMinHeight(140);root.addView(b,new LinearLayout.LayoutParams(-1,-2));}
        setContentView(root);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=1||result!=RESULT_OK||data==null||data.getData()==null)return;
        try(java.io.OutputStream output=getContentResolver().openOutputStream(data.getData(),"wt")){
            if(output==null)throw new java.io.IOException();output.write(report.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            Toast.makeText(this,"Relatório salvo. Nenhum envio automático.",Toast.LENGTH_LONG).show();
        }catch(Exception e){Toast.makeText(this,"Não foi possível salvar.",Toast.LENGTH_LONG).show();}
    }
}
