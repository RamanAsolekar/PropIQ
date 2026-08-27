package com.propiq.field.core

/**
 * Explicit result type for everything that crosses a process/network boundary.
 *
 * [Queued] is not an error — it is the offline-first success path: the work was
 * accepted, persisted to Room, and will be retried by [com.propiq.field.sync.SyncWorker].
 */
sealed interface Outcome<out T> {
    data class Success<T>(val data: T) : Outcome<T>
    data class Queued(val queueId: Long, val reason: FailureKind) : Outcome<Nothing>
    data class Failure(
        val kind: FailureKind,
        val message: String,
        val cause: Throwable? = null,
    ) : Outcome<Nothing>
}

enum class FailureKind {
    NO_NETWORK,
    TIMEOUT,
    BACKEND_UNREACHABLE,
    BACKEND_ERROR,
    UNAUTHORIZED,
    RATE_LIMITED,
    BAD_REQUEST,
    UNKNOWN;

    /** Only these are worth automatically retrying later. */
    val isRetryable: Boolean
        get() = this == NO_NETWORK || this == TIMEOUT ||
            this == BACKEND_UNREACHABLE || this == RATE_LIMITED ||
            this == BACKEND_ERROR
}

/** Field-officer-facing copy. No stack traces, no HTTP jargon. */
fun FailureKind.userMessage(): String = when (this) {
    FailureKind.NO_NETWORK ->
        "No connection. Saved to your device — it will submit automatically when you're back online."
    FailureKind.TIMEOUT ->
        "The valuation engine took too long to respond. Saved and queued for retry."
    FailureKind.BACKEND_UNREACHABLE ->
        "Can't reach the PropIQ server. Check the backend URL in Settings, or stay offline — this is queued."
    FailureKind.BACKEND_ERROR ->
        "The valuation engine hit an internal error. Queued for retry."
    FailureKind.UNAUTHORIZED ->
        "API key rejected. Update the key in Settings and try again."
    FailureKind.RATE_LIMITED ->
        "Rate limit reached (20 assessments/min). Queued — it will retry shortly."
    FailureKind.BAD_REQUEST ->
        "The server rejected these property details. Check the size, age and locality fields."
    FailureKind.UNKNOWN ->
        "Something went wrong. The assessment is saved on this device."
}

fun FailureKind.shortLabel(): String = when (this) {
    FailureKind.NO_NETWORK -> "Offline"
    FailureKind.TIMEOUT -> "Timed out"
    FailureKind.BACKEND_UNREACHABLE -> "Server unreachable"
    FailureKind.BACKEND_ERROR -> "Server error"
    FailureKind.UNAUTHORIZED -> "Auth failed"
    FailureKind.RATE_LIMITED -> "Rate limited"
    FailureKind.BAD_REQUEST -> "Invalid input"
    FailureKind.UNKNOWN -> "Failed"
}
