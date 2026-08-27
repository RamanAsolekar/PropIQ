package com.propiq.field.ui.nav

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.propiq.field.AppContainer
import com.propiq.field.ui.capture.CaptureScreen
import com.propiq.field.ui.capture.CaptureViewModel
import com.propiq.field.ui.home.HomeScreen
import com.propiq.field.ui.home.HomeViewModel
import com.propiq.field.ui.results.ResultsScreen
import com.propiq.field.ui.results.ResultsViewModel

/**
 * Three destinations, deliberately. A jury watching a 3-5 minute pitch has to
 * follow the whole flow without a mental map: Home → Capture → Results.
 * Settings and the offline queue are bottom sheets on Home rather than screens
 * of their own, so the back stack never gets deeper than two.
 */
object Routes {
    const val HOME = "home"
    const val CAPTURE = "capture"
    const val RESULTS = "results/{requestId}"

    fun results(requestId: String) = "results/$requestId"
}

@Composable
fun PropIQNavHost(container: AppContainer) {
    val navController = rememberNavController()
    val context = LocalContext.current

    NavHost(navController = navController, startDestination = Routes.HOME) {

        composable(Routes.HOME) {
            val vm: HomeViewModel = viewModel(
                factory = HomeViewModel.factory(container, context)
            )
            HomeScreen(
                viewModel = vm,
                onStartCapture = { navController.navigate(Routes.CAPTURE) },
                onOpenResult = { navController.navigate(Routes.results(it)) },
            )
        }

        composable(Routes.CAPTURE) {
            val vm: CaptureViewModel = viewModel(
                factory = CaptureViewModel.factory(container, context)
            )
            CaptureScreen(
                viewModel = vm,
                onBack = { navController.popBackStack() },
                onResults = { requestId ->
                    // Replace capture in the stack: backing out of a finished
                    // assessment should land on Home, not on a stale form.
                    navController.navigate(Routes.results(requestId)) {
                        popUpTo(Routes.HOME)
                    }
                },
            )
        }

        composable(
            route = Routes.RESULTS,
            arguments = listOf(navArgument("requestId") { type = NavType.StringType }),
        ) { entry ->
            val requestId = entry.arguments?.getString("requestId").orEmpty()
            val vm: ResultsViewModel = viewModel(
                factory = ResultsViewModel.factory(container)
            )
            ResultsScreen(
                requestId = requestId,
                viewModel = vm,
                onBack = { navController.popBackStack() },
            )
        }
    }
}
