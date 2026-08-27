package com.propiq.field.ui.home

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.propiq.field.AppContainer
import com.propiq.field.core.Outcome
import com.propiq.field.core.userMessage
import com.propiq.field.data.local.AssessmentHistory
import com.propiq.field.data.local.QueuedAssessment
import com.propiq.field.sync.SyncWorker
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val isOnline: Boolean = true,
    val demoMode: Boolean = false,
    val baseUrl: String = "",
    val apiKey: String = "",
    val queued: List<QueuedAssessment> = emptyList(),
    val history: List<AssessmentHistory> = emptyList(),
    val backendStatus: BackendStatus = BackendStatus.Unknown,
    val checkingBackend: Boolean = false,
    val message: String? = null,
) {
    val pendingCount: Int
        get() = queued.count { it.status != QueuedAssessment.STATUS_FAILED_PERMANENT }
}

sealed interface BackendStatus {
    data object Unknown : BackendStatus
    data object Reachable : BackendStatus
    data class Unreachable(val reason: String) : BackendStatus
}

class HomeViewModel(
    private val container: AppContainer,
    private val appContext: Context,
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        HomeUiState(
            baseUrl = container.settings.baseUrl.value,
            apiKey = container.settings.apiKey.value,
            demoMode = container.settings.demoMode.value,
        )
    )
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            container.connectivity.observe().collect { online ->
                _uiState.value = _uiState.value.copy(isOnline = online)
                if (online) SyncWorker.schedule(appContext)
            }
        }
        viewModelScope.launch {
            container.repository.observeQueue().collect {
                _uiState.value = _uiState.value.copy(queued = it)
            }
        }
        viewModelScope.launch {
            container.repository.observeHistory().collect {
                _uiState.value = _uiState.value.copy(history = it)
            }
        }
        viewModelScope.launch {
            container.settings.demoMode.collect {
                _uiState.value = _uiState.value.copy(demoMode = it)
            }
        }
        viewModelScope.launch {
            container.settings.baseUrl.collect {
                _uiState.value = _uiState.value.copy(baseUrl = it)
            }
        }
    }

    fun setDemoMode(enabled: Boolean) {
        container.settings.setDemoMode(enabled)
        _uiState.value = _uiState.value.copy(
            message = if (enabled)
                "Demo Mode on — assessments return the pre-seeded sample instantly, no network."
            else "Demo Mode off — assessments hit the live backend.",
        )
    }

    fun updateBaseUrl(value: String) {
        container.settings.setBaseUrl(value)
        _uiState.value = _uiState.value.copy(
            baseUrl = container.settings.baseUrl.value,
            backendStatus = BackendStatus.Unknown,
        )
    }

    fun updateApiKey(value: String) {
        container.settings.setApiKey(value)
        _uiState.value = _uiState.value.copy(apiKey = container.settings.apiKey.value)
    }

    /** Explicit connectivity test — the thing to press before walking on stage. */
    fun checkBackend() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(checkingBackend = true)
            val status = when (val r = container.repository.pingBackend()) {
                is Outcome.Success -> BackendStatus.Reachable
                is Outcome.Failure -> BackendStatus.Unreachable(r.kind.userMessage())
                is Outcome.Queued -> BackendStatus.Unknown
            }
            _uiState.value = _uiState.value.copy(checkingBackend = false, backendStatus = status)
        }
    }

    fun retryQueueNow() {
        SyncWorker.syncNow(appContext)
        _uiState.value = _uiState.value.copy(message = "Retrying queued assessments…")
    }

    fun discardQueued(id: Long) {
        viewModelScope.launch {
            container.database.queueDao().delete(id)
        }
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }

    companion object {
        fun factory(container: AppContainer, context: Context) = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                HomeViewModel(container, context.applicationContext) as T
        }
    }
}
