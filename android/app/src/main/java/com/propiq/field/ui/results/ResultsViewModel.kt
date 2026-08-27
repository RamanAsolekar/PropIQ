package com.propiq.field.ui.results

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.propiq.field.AppContainer
import com.propiq.field.data.remote.AssessmentResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ResultsUiState(
    val loading: Boolean = true,
    val result: AssessmentResponse? = null,
    val notFound: Boolean = false,
    val exporting: Boolean = false,
    val exportMessage: String? = null,
    val wasDemo: Boolean = false,
)

class ResultsViewModel(
    private val container: AppContainer,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ResultsUiState())
    val uiState: StateFlow<ResultsUiState> = _uiState.asStateFlow()

    fun load(requestId: String) {
        viewModelScope.launch {
            _uiState.value = ResultsUiState(loading = true)
            val row = container.database.historyDao().byId(requestId)
            if (row == null) {
                _uiState.value = ResultsUiState(loading = false, notFound = true)
                return@launch
            }
            val decoded = container.repository.decode(row.resultJson)
            _uiState.value = ResultsUiState(
                loading = false,
                result = decoded,
                notFound = decoded == null,
                wasDemo = row.wasDemo,
            )
        }
    }

    /**
     * Writes the assessment to Downloads as PDF + JSON.
     *
     * Downloads is the folder Office Kit's file bridge surfaces, so the demo's
     * phone-to-laptop hop has a genuine reason to happen: the credit team wants
     * the memo on the laptop, and it is already sitting where the bridge looks.
     */
    fun export() {
        val result = _uiState.value.result ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(exporting = true, exportMessage = null)
            val json = container.repository.encode(result)
            val outcome = runCatching { container.exporter.export(result, json) }
            _uiState.value = _uiState.value.copy(
                exporting = false,
                exportMessage = outcome.getOrNull()?.summary
                    ?: "Could not write to Downloads. Check storage space and try again.",
            )
        }
    }

    fun clearExportMessage() {
        _uiState.value = _uiState.value.copy(exportMessage = null)
    }

    companion object {
        fun factory(container: AppContainer) = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                ResultsViewModel(container) as T
        }
    }
}
