# Keep the names, not every member — r29.
#
# ⚠ `-keep class … { *; }` is a blanket opt-out of shrinking AND obfuscation for the project's
# largest model package, which is far more than "keep the package name" asks for. What actually
# needs members kept is the enums, and the rule below already keeps those. `-keepnames` keeps
# the class names and lets R8 drop what nothing reaches.
-keepnames class com.android.geto.domain.model.**

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
