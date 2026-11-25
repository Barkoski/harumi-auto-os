package com.harumi.autoos;
import android.app.Activity;
import android.content.Intent;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.harumi.autoos.ai.AssistantController;
import org.junit.Test;
import org.junit.runner.RunWith;
import java.lang.reflect.Field;
import static org.junit.Assert.*;
@RunWith(AndroidJUnit4.class)
public class SpeechCaptureRegressionTest {
 @Test public void recognitionSegmentsDoNotCloseTheMicrophonePrematurely()throws Exception{
  var instrumentation=InstrumentationRegistry.getInstrumentation();var context=instrumentation.getTargetContext();
  Activity activity=instrumentation.startActivitySync(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
  Field field=MainActivity.class.getDeclaredField("assistant");field.setAccessible(true);AssistantController assistant=(AssistantController)field.get(activity);
  Field listening=AssistantController.class.getDeclaredField("listening");listening.setAccessible(true);
  instrumentation.runOnMainSync(assistant::listen);
  long deadline=System.currentTimeMillis()+30000;while(!listening.getBoolean(assistant)&&System.currentTimeMillis()<deadline)Thread.sleep(100);
  assertTrue("Silent emulator microphone did not start",listening.getBoolean(assistant));
  try{
   instrumentation.runOnMainSync(()->assistant.onResult("{\"text\":\"harumi\"}"));Thread.sleep(500);
   assertTrue("First recognized segment stopped the microphone",listening.getBoolean(assistant));
   instrumentation.runOnMainSync(()->assistant.onPartialResult("{\"partial\":\"tudo\"}"));Thread.sleep(1000);
   assertTrue("Natural pause interrupted the sentence",listening.getBoolean(assistant));
   instrumentation.runOnMainSync(()->assistant.onResult("{\"text\":\"tudo bem\"}"));
   deadline=System.currentTimeMillis()+5000;while(listening.getBoolean(assistant)&&System.currentTimeMillis()<deadline)Thread.sleep(100);
   assertFalse("Utterance did not finish after endpoint grace",listening.getBoolean(assistant));
   Field webField=MainActivity.class.getDeclaredField("web");webField.setAccessible(true);android.webkit.WebView web=(android.webkit.WebView)webField.get(activity);
   java.util.concurrent.CountDownLatch done=new java.util.concurrent.CountDownLatch(1);String[] transcript={""};
   instrumentation.runOnMainSync(()->web.evaluateJavascript("document.getElementById('conversation').textContent",value->{transcript[0]=value;done.countDown();}));
   assertTrue(done.await(10,java.util.concurrent.TimeUnit.SECONDS));assertTrue("User request did not preserve all segments: "+transcript[0],transcript[0].contains("harumi tudo bem"));
  }finally{instrumentation.runOnMainSync(assistant::cancel);}
 }
}
