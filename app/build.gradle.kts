plugins { id("com.android.application") }
android {
    namespace = "com.harumi.autoos"
    compileSdk = 35
    ndkVersion = "27.2.12479018"
    defaultConfig {
        applicationId = "com.harumi.autoos"
        minSdk = 26
        targetSdk = 34
        versionCode = 17
        versionName = "0.3.15-dev.1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        ndk { abiFilters += listOf("arm64-v8a", "x86_64") }
        externalNativeBuild { cmake { arguments += listOf("-DANDROID_STL=c++_shared", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_OBJECT_PATH_MAX=180") } }
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    buildTypes { release { isMinifyEnabled = false } }
    externalNativeBuild { cmake { path = file("src/main/cpp/CMakeLists.txt"); version = "3.22.1"; buildStagingDirectory = file("../../work/n") } }
    androidResources { noCompress += listOf("gguf", "onnx", "bin", "fst", "f32") }
    packaging { jniLibs { pickFirsts += listOf("**/libc++_shared.so") } }
}
dependencies {
    implementation("androidx.webkit:webkit:1.12.1")
    implementation(files("libs/sherpa-onnx-2.0.1.aar"))
    implementation("org.jetbrains.kotlin:kotlin-stdlib:2.1.0")
    implementation("com.alphacephei:vosk-android:0.3.47@aar")
    implementation("net.java.dev.jna:jna:5.13.0@aar")
    // Roteador offline: GraphHopper 11.1 (mesma versao do grafo gerado no PC). O core vem de app/libs com MMapDataAccess ajustada
    // para Android (gerado por scripts/build-graphhopper-android.sh); as dependencias dele sao declaradas aqui (sem servidor/XML/protobuf).
    implementation(files("libs/graphhopper-core-11.1-android.jar"))
    implementation("com.graphhopper:graphhopper-web-api:11.1")
    implementation("com.carrotsearch:hppc:0.8.1")
    implementation("org.codehaus.janino:janino:3.1.9")
    implementation("de.westnordost:osm-legal-default-speeds-jvm:1.4")
    implementation("org.slf4j:slf4j-api:2.0.17")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
}
