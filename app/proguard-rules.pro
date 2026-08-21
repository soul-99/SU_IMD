# Keep the package name
-keep class com.android.geto.domain.model.** { *; }

# Keep the enum classes and their members (values/names)
-keep enum com.android.geto.domain.model.** {
    *;
}
# ShizukuPermission reflects into Shizuku.newProcess to run `pm grant` — it is private and
# deprecated in the library, so without this R8 is free to rename or remove it and the
# no-PC setup path silently stops working.
-keepclassmembers class rikka.shizuku.Shizuku {
    private static *** newProcess(java.lang.String[], java.lang.String[], java.lang.String);
}
-keep class rikka.shizuku.ShizukuProvider { *; }
