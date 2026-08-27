# Retrofit / Gson DTOs are reflected over — keep their members.
-keep class com.propiq.field.data.remote.** { *; }
-keepattributes Signature, InnerClasses, EnclosingMethod, RuntimeVisibleAnnotations
-dontwarn okhttp3.**
-dontwarn retrofit2.**
