package com.knowOcean.rag;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
@MapperScan("com.knowOcean.rag.**.mapper")
public class KnowOceanBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(KnowOceanBackendApplication.class, args);
        System.out.println("======================================== 系统运行中 ========================================");
    }
}
