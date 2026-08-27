package com.propiq.field.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Query

/**
 * The subset of the PropIQ API the field app actually uses.
 *
 * Endpoint shapes confirmed by reading backend/app/main.py directly:
 *  - /api/v1/assess/image is `multipart/form-data` with EVERY property field as
 *    a separate Form part (main.py:574-597), not a JSON body. Image tags are
 *    four fixed parts `image_tag_0..3`, not a repeated field.
 *  - Auth is a required `X-API-Key` header (core/security.py, auto_error=True) —
 *    there is no anonymous fallback, so a missing key is a 403, not a 401.
 */
interface PropIQApi {

    @GET("/api/v1/health")
    suspend fun health(): Response<Map<String, Any>>

    @GET("/api/v1/localities")
    suspend fun localities(@Query("city") city: String? = null): Response<LocalitiesResponse>

    /**
     * Assessment + CV image scoring.
     *
     * Note the backend rejects a request with zero images (400 "No images
     * provided"), so the capture screen must guarantee at least one part before
     * this is called.
     */
    @Multipart
    @POST("/api/v1/assess/image")
    suspend fun assessWithImage(
        @Part("locality") locality: RequestBody,
        @Part("prop_type") propType: RequestBody,
        @Part("size_sqft") sizeSqft: RequestBody,
        @Part("age_years") ageYears: RequestBody,
        @Part("floor_num") floorNum: RequestBody,
        @Part("is_freehold") isFreehold: RequestBody,
        @Part("is_rera_registered") isReraRegistered: RequestBody,
        @Part("occupancy") occupancy: RequestBody,
        @Part("rental_yield_pct") rentalYieldPct: RequestBody,
        @Part("has_clear_title") hasClearTitle: RequestBody,
        @Part("has_encumbrance") hasEncumbrance: RequestBody,
        @Part("has_legal_dispute") hasLegalDispute: RequestBody,
        @Part("zoning_approved") zoningApproved: RequestBody,
        @Part("geo_lat") geoLat: RequestBody?,
        @Part("geo_lon") geoLon: RequestBody?,
        @Part("image_tag_0") imageTag0: RequestBody,
        @Part("image_tag_1") imageTag1: RequestBody,
        @Part("image_tag_2") imageTag2: RequestBody,
        @Part("image_tag_3") imageTag3: RequestBody,
        @Part images: List<MultipartBody.Part>,
    ): Response<AssessmentResponse>

    @POST("/api/v1/chat")
    suspend fun chat(@Body body: ChatRequestDto): Response<ChatResponseDto>
}
