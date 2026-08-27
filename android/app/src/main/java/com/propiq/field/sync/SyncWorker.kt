package com.propiq.field.sync

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.propiq.field.PropIQApp
import com.propiq.field.core.Outcome
import com.propiq.field.data.local.QueuedAssessment
import com.propiq.field.data.repo.CapturedPhoto
import com.propiq.field.data.repo.FieldAssessmentRequest
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * Drains the offline queue when connectivity returns.
 *
 * Scheduled with a NetworkType.CONNECTED constraint, so WorkManager itself
 * handles the "officer walks out of the basement" trigger — we are not polling
 * or holding a wake lock. Exponential backoff covers the case where the network
 * is technically up but the backend is still cold.
 */
class SyncWorker(
    appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val container = (applicationContext as PropIQApp).container
        val repo = container.repository
        val dao = container.database.queueDao()

        // A previous run may have died mid-flight leaving rows marked syncing.
        dao.releaseStuck()

        val batch = dao.claimBatch()
        if (batch.isEmpty()) return Result.success()

        var anyRetryable = false

        for (item in batch) {
            dao.updateStatus(item.id, QueuedAssessment.STATUS_SYNCING)

            val photos = item.photoPathList.zip(item.photoTagList) { path, tag ->
                CapturedPhoto(path = path, tag = tag)
            }.filter { File(it.path).exists() }

            if (photos.isEmpty()) {
                // The cache was evicted before we got back online. Nothing can
                // be recovered, so retire the row rather than retrying forever.
                dao.markAttemptFailed(
                    item.id,
                    "Captured photos were cleared from device storage.",
                    QueuedAssessment.STATUS_FAILED_PERMANENT,
                )
                continue
            }

            when (val outcome = repo.callAssess(FieldAssessmentRequest.fromQueued(item), photos)) {
                is Outcome.Success -> {
                    repo.persistHistory(outcome.data, wasDemo = false)
                    dao.markSynced(item.id, repo.encode(outcome.data))
                    photos.forEach { runCatching { File(it.path).delete() } }
                }
                is Outcome.Failure -> {
                    if (outcome.kind.isRetryable && item.attemptCount + 1 < QueuedAssessment.MAX_ATTEMPTS) {
                        anyRetryable = true
                        dao.markAttemptFailed(item.id, outcome.message)
                    } else {
                        dao.markAttemptFailed(
                            item.id,
                            outcome.message,
                            QueuedAssessment.STATUS_FAILED_PERMANENT,
                        )
                    }
                }
                is Outcome.Queued -> Unit
            }
        }

        return if (anyRetryable) Result.retry() else Result.success()
    }

    companion object {
        private const val WORK_NAME = "propiq_assessment_sync"

        /**
         * Idempotent — KEEP means repeated calls (every enqueue, every app
         * start) do not stack duplicate workers.
         */
        fun schedule(context: Context) {
            val request = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build()

            WorkManager.getInstance(context)
                .enqueueUniqueWork(WORK_NAME, ExistingWorkPolicy.KEEP, request)
        }

        /** Manual "Retry now" from the queue sheet — replaces any pending run. */
        fun syncNow(context: Context) {
            val request = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .build()

            WorkManager.getInstance(context)
                .enqueueUniqueWork(WORK_NAME, ExistingWorkPolicy.REPLACE, request)
        }
    }
}
