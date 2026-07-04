package com.mykb.server;

import com.mykb.server.common.config.AppSecurityProperties;
import com.mykb.server.common.storage.StorageProperties;
import com.mykb.server.document.config.DocumentProperties;
import com.mykb.server.ocr.config.OcrProperties;
import com.mykb.server.rag.config.RagProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
@EnableConfigurationProperties({
  AppSecurityProperties.class,
  StorageProperties.class,
  DocumentProperties.class,
  OcrProperties.class,
  RagProperties.class
})
public class MyKnowledgeBaseApplication {

  public static void main(String[] args) {
    SpringApplication.run(MyKnowledgeBaseApplication.class, args);
  }
}
