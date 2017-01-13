/*
 * Copyright 2011-2016 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

CCL_NAMESPACE_BEGIN

#ifdef __KERNEL_CUDA__
#define STORAGE_TYPE CUDAFilterStorage
#else
#define STORAGE_TYPE FilterStorage
#endif

ccl_device_inline void kernel_filter_construct_gramian(int x, int y, int storage_ofs, int storage_size, int dx, int dy, int w, int h, float ccl_readonly_ptr buffer, int color_pass, STORAGE_TYPE *storage, float weight, float ccl_readonly_ptr transform, float *XtWX, float3 *XtWY)
{
	const int pass_stride = w*h;

	float ccl_readonly_ptr p_buffer = buffer +      y*w +      x;
	float ccl_readonly_ptr q_buffer = buffer + (y+dy)*w + (x+dx);

	storage += storage_ofs;

#ifdef __KERNEL_CPU__
	transform = storage->transform;
	XtWX += (DENOISE_FEATURES+1)*(DENOISE_FEATURES+1) * storage_ofs;
	XtWY += (DENOISE_FEATURES+1) * storage_ofs;
	const int stride = 1;
	(void)storage_size;
#else
	transform += storage_ofs;
	XtWX += storage_ofs;
	XtWY += storage_ofs;
	const int stride = storage_size;
#endif

	float3 p_color = filter_get_pixel_color(p_buffer + color_pass, pass_stride);
	float3 q_color = filter_get_pixel_color(q_buffer + color_pass, pass_stride);

	float p_std_dev = sqrtf(filter_get_pixel_variance(p_buffer + color_pass, pass_stride));
	float q_std_dev = sqrtf(filter_get_pixel_variance(q_buffer + color_pass, pass_stride));

	if(average(fabs(p_color - q_color)) > 3.0f*(p_std_dev + q_std_dev + 1e-3f)) {
		return;
	}

	float feature_means[DENOISE_FEATURES], features[DENOISE_FEATURES];
	filter_get_features(make_int3(x, y, 0), p_buffer, feature_means, NULL, pass_stride);

	float design_row[DENOISE_FEATURES+1];
	filter_get_design_row_transform(make_int3(x+dx, y+dy, 0), q_buffer, feature_means, pass_stride, features, storage->rank, design_row, transform, stride);

	math_trimatrix_add_gramian_strided(XtWX, storage->rank+1, design_row, weight, stride);
	math_vec3_add_strided(XtWY, storage->rank+1, design_row, weight * q_color, stride);
}

ccl_device_inline void kernel_filter_finalize(int x, int y, int storage_ofs, int storage_size, int w, int h, float *buffer, STORAGE_TYPE *storage, float *XtWX, float3 *XtWY, int4 buffer_params, int sample)
{
	storage += storage_ofs;
#ifdef __KERNEL_CPU__
	XtWX += (DENOISE_FEATURES+1)*(DENOISE_FEATURES+1) * storage_ofs;
	XtWY += (DENOISE_FEATURES+1) * storage_ofs;
	const int stride = 1;
	(void)storage_size;
#else
	XtWX += storage_ofs;
	XtWY += storage_ofs;
	const int stride = storage_size;
#endif

	math_trimatrix_vec3_solve(XtWX, XtWY, storage->rank+1, stride);

	float3 final_color = XtWY[0];
	float *combined_buffer = buffer + (y*buffer_params.y + x + buffer_params.x)*buffer_params.z;
	final_color *= sample;
	if(buffer_params.w) {
		final_color.x += combined_buffer[buffer_params.w+0];
		final_color.y += combined_buffer[buffer_params.w+1];
		final_color.z += combined_buffer[buffer_params.w+2];
	}
	combined_buffer[0] = final_color.x;
	combined_buffer[1] = final_color.y;
	combined_buffer[2] = final_color.z;
}

ccl_device void kernel_filter_reconstruct(KernelGlobals *kg, int sample, float ccl_readonly_ptr buffer, int x, int y, int offset, int stride, float *buffers, int filtered_passes, int2 color_passes, STORAGE_TYPE *storage, float *weight_cache, float ccl_readonly_ptr transform, int transform_stride, int4 filter_area, int4 rect)
{
#if 0
	int buffer_w = align_up(rect.z - rect.x, 4);
	int buffer_h = (rect.w - rect.y);
	int pass_stride = buffer_h * buffer_w * kernel_data.film.num_frames;
	color_passes *= pass_stride;
	int num_frames = kernel_data.film.num_frames;
	int prev_frames = kernel_data.film.prev_frames;

	int2 low  = make_int2(max(rect.x, x - kernel_data.integrator.half_window),
	                      max(rect.y, y - kernel_data.integrator.half_window));
	int2 high = make_int2(min(rect.z, x + kernel_data.integrator.half_window + 1),
	                      min(rect.w, y + kernel_data.integrator.half_window + 1));

	float ccl_readonly_ptr pixel_buffer;
	float ccl_readonly_ptr center_buffer = buffer + (y - rect.y) * buffer_w + (x - rect.x);
	int3 pixel;

	float3 center_color  = filter_get_pixel_color(center_buffer + color_passes.x, pass_stride);
	float sqrt_center_variance = sqrtf(filter_get_pixel_variance(center_buffer + color_passes.x, pass_stride));

	/* NFOR weighting directly writes to the design row, so it doesn't need the feature vector and always uses full rank. */
#  ifdef __KERNEL_CUDA__
	/* On GPUs, store the feature vector in shared memory for faster access. */
	__shared__ float shared_features[DENOISE_FEATURES*CUDA_THREADS_BLOCK_WIDTH*CUDA_THREADS_BLOCK_WIDTH];
	float *features = shared_features + DENOISE_FEATURES*(threadIdx.y*blockDim.x + threadIdx.x);
#  else
	float features[DENOISE_FEATURES];
#  endif
	const int rank = storage->rank;
	const int matrix_size = rank+1;

	float feature_means[DENOISE_FEATURES];
	filter_get_features(make_int3(x, y, 0), center_buffer, feature_means, NULL, pass_stride);

	/* Essentially, this function is just a first-order regression solver.
	 * We model the pixel color as a linear function of the feature vectors.
	 * So, we search the parameters S that minimize W*(X*S - y), where:
	 * - X is the design matrix containing all the feature vectors
	 * - y is the vector containing all the pixel colors
	 * - W is the diagonal matrix containing all pixel weights
	 * Since this is just regular least-squares, the solution is given by:
	 * S = inv(Xt*W*X)*Xt*W*y */

	float XtWX[(DENOISE_FEATURES+1)*(DENOISE_FEATURES+1)], design_row[DENOISE_FEATURES+1];
	float3 solution[(DENOISE_FEATURES+1)];

	math_trimatrix_zero(XtWX, matrix_size);
	math_vec3_zero(solution, matrix_size);
	/* Construct Xt*W*X matrix and Xt*W*y vector (and fill weight cache, if used). */
	FOR_PIXEL_WINDOW {
		float3 color = filter_get_pixel_color(pixel_buffer + color_passes.x, pass_stride);
		float variance = filter_get_pixel_variance(pixel_buffer + color_passes.x, pass_stride);
		if(filter_firefly_rejection(color, variance, center_color, sqrt_center_variance)) {
#ifdef WEIGHT_CACHING_CUDA
			if(cache_idx < CUDA_WEIGHT_CACHE_SIZE) weight_cache[cache_idx] = 0.0f;
#elif defined(WEIGHT_CACHING_CPU)
			weight_cache[cache_idx] = 0.0f;
#endif
			continue;
		}

		filter_get_design_row_transform(pixel, pixel_buffer, feature_means, pass_stride, features, rank, design_row, transform, transform_stride);
		float weight = nlm_weight(x, y, pixel.x, pixel.y, center_buffer + color_passes.y, pixel_buffer + color_passes.y, pass_stride, 1.0f, kernel_data.integrator.weighting_adjust, 4, rect);

		if(weight < 1e-5f) {
#ifdef WEIGHT_CACHING_CUDA
			if(cache_idx < CUDA_WEIGHT_CACHE_SIZE) weight_cache[cache_idx] = 0.0f;
#elif defined(WEIGHT_CACHING_CPU)
			weight_cache[cache_idx] = 0.0f;
#endif
			continue;
		}
		weight /= max(1.0f, variance);
		weight_cache[cache_idx] = weight;

		math_trimatrix_add_gramian(XtWX, matrix_size, design_row, weight);
		math_vec3_add(solution, matrix_size, design_row, weight * color);
	} END_FOR_PIXEL_WINDOW

	math_trimatrix_vec3_solve(XtWX, solution, matrix_size);

	if(kernel_data.integrator.use_gradients) {
		FOR_PIXEL_WINDOW {
			float weight;
			float3 color;
#if defined(WEIGHTING_CACHING_CPU) || defined(WEIGHTING_CACHING_CUDA)
#  ifdef WEIGHTING_CACHING_CUDA
			if(cache_idx < CUDA_WEIGHT_CACHE_SIZE)
#  endif
			{
				weight = weight_cache[cache_idx];
				if(weight == 0.0f) continue;
				color = filter_get_pixel_color(pixel_buffer + color_passes.x, pass_stride);
				filter_get_design_row_transform(pixel, pixel_buffer, feature_means, pass_stride, features, rank, design_row, transform, transform_stride);
			}
#  ifdef WEIGHTING_CACHING_CUDA
			else
#  endif
#endif
#ifndef WEIGHTING_CACHING_CPU
			{
				color = filter_get_pixel_color(pixel_buffer + color_passes.x, pass_stride);
				float variance = filter_get_pixel_variance(pixel_buffer + color_passes.x, pass_stride);
				if(filter_firefly_rejection(color, variance, center_color, sqrt_center_variance)) continue;

				filter_get_design_row_transform(pixel, pixel_buffer, feature_means, pass_stride, features, rank, design_row, transform, transform_stride);
				weight = nlm_weight(x, y, pixel.x, pixel.y, center_buffer + color_passes.y, pixel_buffer + color_passes.y, pass_stride, 1.0f, kernel_data.integrator.weighting_adjust, 4, rect);

				if(weight == 0.0f) continue;
				weight /= max(1.0f, variance);
			}
#endif

			float3 reconstruction = math_vector_vec3_dot(design_row, solution, matrix_size);
#ifdef OUTPUT_RENDERBUFFER
			if(pixel.y >= filter_area.y && pixel.y < filter_area.y+filter_area.w && pixel.x >= filter_area.x && pixel.x < filter_area.x+filter_area.z) {
				float *combined_buffer = buffers + (offset + pixel.y*stride + pixel.x)*kernel_data.film.pass_stride;
				atomic_add_and_fetch_float(combined_buffer + 0, weight*reconstruction.x);
				atomic_add_and_fetch_float(combined_buffer + 1, weight*reconstruction.y);
				atomic_add_and_fetch_float(combined_buffer + 2, weight*reconstruction.z);
				atomic_add_and_fetch_float(combined_buffer + 3, weight);
			}
#elif defined(OUTPUT_DENOISEBUFFER)
			float *filtered_buffer = ((float*) pixel_buffer) + filtered_passes*pass_stride;
			atomic_add_and_fetch_float(filtered_buffer + 0*pass_stride, weight*reconstruction.x);
			atomic_add_and_fetch_float(filtered_buffer + 1*pass_stride, weight*reconstruction.y);
			atomic_add_and_fetch_float(filtered_buffer + 2*pass_stride, weight*reconstruction.z);
			atomic_add_and_fetch_float(filtered_buffer + 3*pass_stride, weight);
#endif
			
		} END_FOR_PIXEL_WINDOW
	}
	else {
		float3 final_color = solution[0];
#ifdef OUTPUT_RENDERBUFFER
		float *combined_buffer = buffers + (offset + y*stride + x)*kernel_data.film.pass_stride;
		final_color *= sample;
		if(kernel_data.film.pass_no_denoising) {
			final_color.x += combined_buffer[kernel_data.film.pass_no_denoising+0];
			final_color.y += combined_buffer[kernel_data.film.pass_no_denoising+1];
			final_color.z += combined_buffer[kernel_data.film.pass_no_denoising+2];
		}
		combined_buffer[0] = final_color.x;
		combined_buffer[1] = final_color.y;
		combined_buffer[2] = final_color.z;
#elif defined(OUTPUT_DENOISEBUFFER)
		float *filtered_buffer = ((float*) center_buffer) + filtered_passes*pass_stride;
		filtered_buffer[0*pass_stride] = final_color.x;
		filtered_buffer[1*pass_stride] = final_color.y;
		filtered_buffer[2*pass_stride] = final_color.z;
		filtered_buffer[3*pass_stride] = 1.0f;
#endif
	}
#endif
}

#undef STORAGE_TYPE

CCL_NAMESPACE_END