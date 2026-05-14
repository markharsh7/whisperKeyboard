#include "whisper_jni.h"
#include "whisper.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>
#include <android/log.h>

#define TAG "WhisperJNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)

struct WhisperContext {
    struct whisper_context * ctx = nullptr;
    struct whisper_full_params params;
};

static std::string jstringToString(JNIEnv *env, jstring jstr) {
    if (!jstr) return "";
    const char *cstr = env->GetStringUTFChars(jstr, nullptr);
    std::string result(cstr);
    env->ReleaseStringUTFChars(jstr, cstr);
    return result;
}

static jstring stringToJstring(JNIEnv *env, const std::string &str) {
    return env->NewStringUTF(str.c_str());
}

// Read 16-bit mono WAV and return float samples
static std::vector<float> readWavFloats(const std::string &path) {
    std::vector<float> samples;

    FILE *f = fopen(path.c_str(), "rb");
    if (!f) {
        LOGE("Failed to open audio file: %s", path.c_str());
        return samples;
    }

    // Read WAV header
    char chunk_id[4];
    int32_t chunk_size;
    char format[4];
    char subchunk1_id[4];
    int32_t subchunk1_size;
    int16_t audio_format;
    int16_t num_channels;
    int32_t sample_rate;
    int32_t byte_rate;
    int16_t block_align;
    int16_t bits_per_sample;

    if (fread(chunk_id, 1, 4, f) != 4) goto error;
    if (fread(&chunk_size, 4, 1, f) != 1) goto error;
    if (fread(format, 1, 4, f) != 4) goto error;
    if (fread(subchunk1_id, 1, 4, f) != 4) goto error;
    if (fread(&subchunk1_size, 4, 1, f) != 1) goto error;
    if (fread(&audio_format, 2, 1, f) != 1) goto error;
    if (fread(&num_channels, 2, 1, f) != 1) goto error;
    if (fread(&sample_rate, 4, 1, f) != 1) goto error;
    if (fread(&byte_rate, 4, 1, f) != 1) goto error;
    if (fread(&block_align, 2, 1, f) != 1) goto error;
    if (fread(&bits_per_sample, 2, 1, f) != 1) goto error;

    // Skip to "data" chunk
    char data_id[4];
    int32_t data_size;
    while (1) {
        if (fread(data_id, 1, 4, f) != 4) goto error;
        if (fread(&data_size, 4, 1, f) != 1) goto error;
        if (strncmp(data_id, "data", 4) == 0) break;
        fseek(f, data_size, SEEK_CUR);
    }

    if (bits_per_sample != 16) {
        LOGE("Unsupported bit depth: %d (expected 16)", bits_per_sample);
        goto error;
    }

    {
        int num_samples = data_size / (bits_per_sample / 8);
        std::vector<int16_t> pcm16(num_samples);
        size_t read_count = fread(pcm16.data(), sizeof(int16_t), num_samples, f);
        fclose(f);

        if (read_count != (size_t)num_samples) {
            LOGE("Short read: got %zu, expected %d", read_count, num_samples);
        }

        // Convert to float in [-1.0, 1.0]
        samples.resize(num_samples);
        for (int i = 0; i < num_samples; i++) {
            samples[i] = pcm16[i] / 32768.0f;
        }

        // If stereo, keep only the first channel (mono)
        if (num_channels > 1) {
            int mono_samples = num_samples / num_channels;
            std::vector<float> mono(mono_samples);
            for (int i = 0; i < mono_samples; i++) {
                mono[i] = samples[i * num_channels];
            }
            samples = std::move(mono);
        }

        // Resample to 16kHz if needed (simple linear interpolation)
        if (sample_rate != WHISPER_SAMPLE_RATE && sample_rate > 0) {
            double ratio = (double)WHISPER_SAMPLE_RATE / sample_rate;
            int new_len = (int)(samples.size() * ratio);
            std::vector<float> resampled(new_len);
            for (int i = 0; i < new_len; i++) {
                double src_idx = i / ratio;
                int idx0 = (int)src_idx;
                int idx1 = idx0 + 1;
                if (idx1 >= (int)samples.size()) idx1 = idx0;
                double frac = src_idx - idx0;
                resampled[i] = samples[idx0] * (1.0 - frac) + samples[idx1] * frac;
            }
            samples = std::move(resampled);
        }
    }

    return samples;

error:
    LOGE("Failed to parse WAV file: %s", path.c_str());
    if (f) fclose(f);
    return std::vector<float>();
}

JNIEXPORT jlong JNICALL
Java_com_whisperkeyboard_WhisperEngine_nativeInit(JNIEnv *env, jobject /*thiz*/,
    jstring modelPath, jboolean useGpu) {

    std::string path = jstringToString(env, modelPath);
    LOGI("Initializing whisper from: %s", path.c_str());

    struct whisper_context_params cparams = whisper_context_default_params();
    cparams.use_gpu = useGpu;

    struct whisper_context *ctx = whisper_init_from_file_with_params(path.c_str(), cparams);
    if (!ctx) {
        LOGE("Failed to initialize whisper context");
        return 0;
    }

    auto *wc = new WhisperContext();
    wc->ctx = ctx;
    wc->params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    wc->params.print_progress = false;
    wc->params.print_realtime = false;
    wc->params.print_timestamps = false;
    wc->params.no_timestamps = true;
    wc->params.single_segment = false;
    wc->params.max_len = 0; // no limit
    wc->params.language = nullptr; // auto-detect

    LOGI("Whisper initialized successfully");
    return reinterpret_cast<jlong>(wc);
}

JNIEXPORT jstring JNICALL
Java_com_whisperkeyboard_WhisperEngine_nativeTranscribe(JNIEnv *env, jobject /*thiz*/,
    jlong contextPtr, jstring audioPath, jstring language, jint nThreads) {

    if (contextPtr == 0) {
        LOGE("Invalid context pointer");
        return stringToJstring(env, "");
    }

    auto *wc = reinterpret_cast<WhisperContext *>(contextPtr);
    if (!wc->ctx) {
        LOGE("Null whisper context");
        return stringToJstring(env, "");
    }

    std::string audio_path = jstringToString(env, audioPath);
    LOGI("Transcribing: %s", audio_path.c_str());

    std::vector<float> samples = readWavFloats(audio_path);
    if (samples.empty()) {
        LOGE("No audio samples read");
        return stringToJstring(env, "");
    }

    LOGI("Audio: %zu samples (%.1f seconds)", samples.size(), (float)samples.size() / WHISPER_SAMPLE_RATE);

    // Set language if provided
    if (language) {
        std::string lang = jstringToString(env, language);
        if (!lang.empty() && lang != "auto") {
            wc->params.language = lang.c_str();
        } else {
            wc->params.language = nullptr;
        }
    }

    wc->params.n_threads = nThreads > 0 ? nThreads : std::min(4, (int)std::thread::hardware_concurrency());

    int ret = whisper_full(wc->ctx, wc->params, samples.data(), (int)samples.size());
    if (ret != 0) {
        LOGE("whisper_full failed with code %d", ret);
        return stringToJstring(env, "");
    }

    int n_segments = whisper_full_n_segments(wc->ctx);
    std::string result;

    for (int i = 0; i < n_segments; i++) {
        const char *text = whisper_full_get_segment_text(wc->ctx, i);
        if (text && strlen(text) > 0) {
            if (!result.empty()) result += " ";
            result += text;
        }
    }

    // Strip leading/trailing whitespace
    while (!result.empty() && result.front() == ' ') result.erase(0, 1);
    while (!result.empty() && result.back() == ' ') result.pop_back();

    LOGI("Transcription: \"%s\"", result.c_str());
    return stringToJstring(env, result);
}

JNIEXPORT void JNICALL
Java_com_whisperkeyboard_WhisperEngine_nativeDestroy(JNIEnv */*env*/, jobject /*thiz*/,
    jlong contextPtr) {

    if (contextPtr == 0) return;

    auto *wc = reinterpret_cast<WhisperContext *>(contextPtr);
    if (wc->ctx) {
        whisper_free(wc->ctx);
        wc->ctx = nullptr;
    }
    delete wc;

    LOGI("Whisper context destroyed");
}
