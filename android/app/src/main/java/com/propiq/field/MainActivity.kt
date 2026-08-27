package com.propiq.field

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.propiq.field.ui.nav.PropIQNavHost
import com.propiq.field.ui.theme.PropIQTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        val container = (application as PropIQApp).container
        setContent {
            PropIQTheme {
                PropIQNavHost(container = container)
            }
        }
    }
}
