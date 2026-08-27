package com.propiq.field

import com.propiq.field.core.FailureKind
import com.propiq.field.core.userMessage
import com.propiq.field.data.demo.Localities
import com.propiq.field.data.remote.AssessmentResponse
import com.propiq.field.data.remote.RiskFlag
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * The offline queue's whole value rests on one judgement: which failures are
 * worth retrying. Get it wrong in one direction and a field officer loses work;
 * get it wrong in the other and the queue fills with requests that can never
 * succeed and will be retried eight times each.
 */
class FailureRoutingTest {

    @Test
    fun `transient failures are retryable`() {
        assertTrue(FailureKind.NO_NETWORK.isRetryable)
        assertTrue(FailureKind.TIMEOUT.isRetryable)
        assertTrue(FailureKind.BACKEND_UNREACHABLE.isRetryable)
        assertTrue(FailureKind.RATE_LIMITED.isRetryable)
        // The backend rate-limits /assess/image at 20/min — a burst of site
        // visits legitimately hits this and must not lose data.
        assertTrue(FailureKind.BACKEND_ERROR.isRetryable)
    }

    @Test
    fun `deterministic failures are never retried`() {
        // A 422 from bad property fields and a 403 from a wrong API key will
        // fail identically forever. Queueing them just builds a poison backlog.
        assertFalse(FailureKind.BAD_REQUEST.isRetryable)
        assertFalse(FailureKind.UNAUTHORIZED.isRetryable)
    }

    @Test
    fun `every failure kind has field-officer-readable copy`() {
        FailureKind.entries.forEach { kind ->
            val msg = kind.userMessage()
            assertTrue("${kind.name} has no message", msg.isNotBlank())
            // No stack traces, no HTTP jargon leaking to someone standing in a
            // stranger's living room.
            assertFalse("${kind.name} leaks HTTP jargon", msg.contains("HTTP"))
            assertFalse("${kind.name} leaks an exception name", msg.contains("Exception"))
        }
    }
}

/**
 * The results screen promises the fraud signal is impossible to miss. That
 * promise is implemented by [AssessmentResponse.fraudAlert] and
 * [AssessmentResponse.rankedFlags], so both are pinned here.
 */
class AssessmentResponseTest {

    private fun flag(name: String, severity: String) =
        RiskFlag(flag = name, severity = severity, detail = "detail")

    @Test
    fun `fraudAlert picks up all three fraud-class flags`() {
        listOf(
            "cv_property_type_mismatch",
            "cv_fraud_detected",
            "vector_duplicate_collateral",
        ).forEach { name ->
            val r = AssessmentResponse(riskFlags = listOf(flag(name, "high")))
            assertNotNull("$name should raise a fraud alert", r.fraudAlert)
        }
    }

    @Test
    fun `an ordinary flag is not a fraud alert`() {
        val r = AssessmentResponse(riskFlags = listOf(flag("cv_poor_condition", "high")))
        assertNull(r.fraudAlert)
    }

    @Test
    fun `flags rank high severity first`() {
        val r = AssessmentResponse(
            riskFlags = listOf(
                flag("low_one", "low"),
                flag("high_one", "high"),
                flag("medium_one", "medium"),
            )
        )
        assertEquals(listOf("high_one", "medium_one", "low_one"), r.rankedFlags.map { it.flag })
    }

    @Test
    fun `an absent risk_flags block does not crash the screen`() {
        // The backend omits blocks entirely when an optional dependency is
        // missing server-side, so null is a normal case, not a bug.
        val r = AssessmentResponse()
        assertTrue(r.rankedFlags.isEmpty())
        assertNull(r.fraudAlert)
        assertEquals(8.3, r.resolvedMape, 1e-9)
    }

    @Test
    fun `time to sell falls back to the liquidity profile`() {
        // The backend puts this at top level AND inside liquidity_profile;
        // ResultsDashboard.js falls back between them and so must we.
        val nested = AssessmentResponse(
            liquidityProfile = com.propiq.field.data.remote.LiquidityProfile(
                timeToSellDays = listOf(28, 62)
            )
        )
        assertEquals(listOf(28, 62), nested.resolvedTimeToSell)

        val topLevel = AssessmentResponse(timeToSellDays = listOf(10, 20))
        assertEquals(listOf(10, 20), topLevel.resolvedTimeToSell)
    }
}

/**
 * Localities.kt is generated from backend/app/data/india_circle_rates.py. If the
 * two drift apart the picker starts offering names the valuation model does not
 * know, and get_circle_rate() silently returns a default rate — a wrong number
 * with no error anywhere.
 */
class LocalitiesTest {

    @Test
    fun `all three pilot cities are represented`() {
        Localities.cities.forEach { city ->
            assertTrue("$city has no localities", Localities.forCity(city).isNotEmpty())
        }
    }

    @Test
    fun `lookup is case insensitive`() {
        assertEquals("Baner", Localities.byName("baner")?.name)
        assertEquals("Baner", Localities.byName("BANER")?.name)
        assertNull(Localities.byName("Nowhere-on-Sea"))
    }

    @Test
    fun `every locality carries plausible Indian coordinates`() {
        Localities.all.forEach {
            assertTrue("${it.name} latitude out of range", it.lat in 6.0..38.0)
            assertTrue("${it.name} longitude out of range", it.lon in 68.0..98.0)
            assertTrue("${it.name} has no zone tier", it.zoneTier.isNotBlank())
        }
    }

    @Test
    fun `nearest locality resolves a Baner coordinate to Baner`() {
        // Standing in Baner should pre-select Baner, not Kothrud.
        val fix = com.propiq.field.location.GeoFix(lat = 18.5590, lon = 73.7868)
        assertEquals("Baner", fix.nearestLocality(Localities.coordinateMap("Pune")))
    }

    @Test
    fun `zone tiers use the vocabulary the LTV engine expects`() {
        // ltv_audit.py branches on exactly these three strings.
        val allowed = setOf("prime", "mid", "peripheral")
        Localities.all.forEach {
            assertTrue("${it.name} has unknown tier ${it.zoneTier}", it.zoneTier in allowed)
        }
    }
}
