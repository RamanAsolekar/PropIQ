package com.propiq.field.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface QueueDao {

    @Insert
    suspend fun insert(item: QueuedAssessment): Long

    /** Drives the Home screen's live "N queued" pill. */
    @Query(
        "SELECT * FROM queued_assessments WHERE status != :synced " +
            "ORDER BY created_at DESC"
    )
    fun observeOutstanding(synced: String = QueuedAssessment.STATUS_SYNCED): Flow<List<QueuedAssessment>>

    @Query("SELECT COUNT(*) FROM queued_assessments WHERE status = :status")
    fun observePendingCount(status: String = QueuedAssessment.STATUS_PENDING): Flow<Int>

    /**
     * Claimed by the sync worker. Ordered oldest-first so a backlog drains in
     * the order the officer actually walked the properties.
     */
    @Query(
        "SELECT * FROM queued_assessments WHERE status = :status " +
            "AND attempt_count < :maxAttempts ORDER BY created_at ASC LIMIT :limit"
    )
    suspend fun claimBatch(
        limit: Int = 5,
        status: String = QueuedAssessment.STATUS_PENDING,
        maxAttempts: Int = QueuedAssessment.MAX_ATTEMPTS,
    ): List<QueuedAssessment>

    @Query("UPDATE queued_assessments SET status = :status WHERE id = :id")
    suspend fun updateStatus(id: Long, status: String)

    @Query(
        "UPDATE queued_assessments SET status = :status, attempt_count = attempt_count + 1, " +
            "last_error = :error WHERE id = :id"
    )
    suspend fun markAttemptFailed(id: Long, error: String, status: String = QueuedAssessment.STATUS_PENDING)

    @Query(
        "UPDATE queued_assessments SET status = :status, result_json = :json, " +
            "last_error = NULL WHERE id = :id"
    )
    suspend fun markSynced(
        id: Long,
        json: String,
        status: String = QueuedAssessment.STATUS_SYNCED,
    )

    @Query("DELETE FROM queued_assessments WHERE id = :id")
    suspend fun delete(id: Long)

    @Query("SELECT COUNT(*) FROM queued_assessments WHERE status = :status")
    suspend fun countPending(status: String = QueuedAssessment.STATUS_PENDING): Int

    /** Resets rows orphaned mid-flight by a process death. */
    @Query(
        "UPDATE queued_assessments SET status = :pending WHERE status = :syncing"
    )
    suspend fun releaseStuck(
        pending: String = QueuedAssessment.STATUS_PENDING,
        syncing: String = QueuedAssessment.STATUS_SYNCING,
    )
}

@Dao
interface HistoryDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(item: AssessmentHistory)

    @Query("SELECT * FROM assessment_history ORDER BY created_at DESC LIMIT :limit")
    fun observeRecent(limit: Int = 20): Flow<List<AssessmentHistory>>

    @Query("SELECT * FROM assessment_history WHERE requestId = :id")
    suspend fun byId(id: String): AssessmentHistory?

    @Query("DELETE FROM assessment_history")
    suspend fun clear()
}
