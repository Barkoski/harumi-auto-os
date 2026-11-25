plugins { id("com.android.application") }
android {
    namespace = "com.harumi.compat"
    compileSdk = 35
    defaultConfig { applicationId = "com.harumi.compat"; minSdk = 26; targetSdk = 34; versionCode = 1; versionName = "1.0.0" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    sourceSets.getByName("main").java {
        srcDirs("src/main/java", "../app/src/main/java/com/harumi/autoos/domain", "../app/src/main/java/com/harumi/autoos/oem")
    }
}
